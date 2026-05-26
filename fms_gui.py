from __future__ import annotations

import ctypes
import os
import queue
import shlex
import subprocess
import threading
import time
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# tempo entre uma leitura e outra do processo
POLL_INTERVAL_SECONDS = 0.20

# guardo so as ultimas linhas pra nao crescer sem fim
CAPTURED_LINES_LIMIT = 50


@dataclass
class Limits:
    # limites pedidos na interface
    cpu_quota_seconds: float
    timeout_seconds: float | None
    max_memory_bytes: int | None
    stdin_payload: str | None


@dataclass
class Metrics:
    # dados que vao aparecer no relatorio final
    user_cpu_seconds: float = 0.0
    system_cpu_seconds: float = 0.0
    total_cpu_seconds: float = 0.0
    peak_memory_bytes: int = 0


@dataclass
class RunResult:
    # resumo da execucao
    command_display: str
    exit_code: int | None
    reason: str
    wall_time_seconds: float
    metrics: Metrics
    stdout_tail: list[str]
    stderr_tail: list[str]


class ProcessProbe:
    # classe base so pra manter a mesma ideia entre windows e linux
    def snapshot(self) -> Metrics:
        raise NotImplementedError

    def terminate(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        process.terminate()

    def close(self) -> None:
        return None


class LinuxProcessProbe(ProcessProbe):
    # deixei isso pq as vezes testo fora do windows tambem
    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.clock_ticks = os.sysconf("SC_CLK_TCK")
        self.status_path = Path(f"/proc/{pid}/status")
        self.stat_path = Path(f"/proc/{pid}/stat")

    def snapshot(self) -> Metrics:
        metrics = Metrics()

        try:
            stat_parts = self.stat_path.read_text(encoding="utf-8").split()
            metrics.user_cpu_seconds = int(stat_parts[13]) / self.clock_ticks
            metrics.system_cpu_seconds = int(stat_parts[14]) / self.clock_ticks
        except (FileNotFoundError, IndexError, OSError, ValueError):
            return metrics

        metrics.total_cpu_seconds = (
            metrics.user_cpu_seconds + metrics.system_cpu_seconds
        )

        try:
            for line in self.status_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmHWM:"):
                    metrics.peak_memory_bytes = int(line.split()[1]) * 1024
                    break
        except (FileNotFoundError, OSError, ValueError):
            pass

        return metrics


class WindowsClock:
    # aqui uso a sugestao do prof: GetTickCount64 de sysinfoapi.h
    def __init__(self) -> None:
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.GetTickCount64.restype = ctypes.c_ulonglong

    def now_seconds(self) -> float:
        return self.kernel32.GetTickCount64() / 1000.0


class WindowsProcessProbe(ProcessProbe):
    # valores padrao de permissao pra abrir o processo
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_VM_READ = 0x0010

    class FILETIME(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", ctypes.c_ulong),
            ("dwHighDateTime", ctypes.c_ulong),
        ]

    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]

    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.psapi = ctypes.WinDLL("psapi", use_last_error=True)

        # OpenProcess e GetProcessTimes sao da parte de processthreadsapi.h
        self.handle = self.kernel32.OpenProcess(
            self.PROCESS_QUERY_LIMITED_INFORMATION | self.PROCESS_VM_READ,
            False,
            pid,
        )

    def snapshot(self) -> Metrics:
        metrics = Metrics()
        if not self.handle:
            return metrics

        creation = self.FILETIME()
        exit_time = self.FILETIME()
        kernel = self.FILETIME()
        user = self.FILETIME()

        if self.kernel32.GetProcessTimes(
            self.handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            metrics.user_cpu_seconds = self._filetime_to_seconds(user)
            metrics.system_cpu_seconds = self._filetime_to_seconds(kernel)
            metrics.total_cpu_seconds = (
                metrics.user_cpu_seconds + metrics.system_cpu_seconds
            )

        counters = self.PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(self.PROCESS_MEMORY_COUNTERS_EX)
        if self.psapi.GetProcessMemoryInfo(
            self.handle,
            ctypes.byref(counters),
            counters.cb,
        ):
            metrics.peak_memory_bytes = int(counters.PeakWorkingSetSize)

        return metrics

    def terminate(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return

        # tento matar direto pela API do windows, se falhar cai no terminate normal
        if self.handle and self.kernel32.TerminateProcess(self.handle, 1):
            return

        super().terminate(process)

    def close(self) -> None:
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None

    @staticmethod
    def _filetime_to_seconds(filetime: FILETIME) -> float:
        value = (filetime.dwHighDateTime << 32) | filetime.dwLowDateTime
        return value / 10_000_000.0


def build_process_probe(pid: int) -> ProcessProbe:
    # escolhe o jeito certo de medir conforme o sistema
    if os.name == "nt":
        return WindowsProcessProbe(pid)
    return LinuxProcessProbe(pid)


def monotonic_seconds() -> float:
    # no windows mantive usando a API sugerida
    if os.name == "nt":
        return WindowsClock().now_seconds()
    return time.monotonic()


def parse_command_line(command_line: str) -> list[str]:
    # separa o texto digitado em partes, respeitando aspas
    return shlex.split(command_line, posix=os.name != "nt")


def build_command(executable: str, arguments: str) -> list[str]:
    # junta binario + argumentos num formato que o Popen entende
    tokens = [executable.strip()]
    if arguments.strip():
        tokens.extend(parse_command_line(arguments))
    return [token for token in tokens if token]


def format_seconds(value: float) -> str:
    return f"{value:.3f} s"


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def read_stream(
    stream,
    label: str,
    sink: deque[str],
    ui_queue: queue.Queue[tuple[str, object]],
) -> None:
    # essa thread so fica lendo a saida do processo
    try:
        for raw_line in iter(stream.readline, ""):
            line = raw_line.rstrip("\r\n")
            sink.append(line)
            ui_queue.put(("log", f"[{label}] {line}"))
    finally:
        stream.close()


def timeout_monitor(
    timeout_seconds: float | None,
    stop_event: threading.Event,
    timeout_events: queue.Queue[str],
) -> None:
    # a thread de timeout nao mata o processo direto
    # ela so avisa a thread principal por fila
    if timeout_seconds is None:
        return

    timed_out = not stop_event.wait(timeout_seconds)
    if timed_out:
        timeout_events.put("timeout_expired")


def terminate_process(
    process: subprocess.Popen[str],
    probe: ProcessProbe,
) -> None:
    if process.poll() is not None:
        return

    probe.terminate(process)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def send_optional_stdin(process: subprocess.Popen[str], payload: str | None) -> None:
    # se a pessoa quiser, manda uma linha pro programa monitorado
    if process.stdin is None:
        return

    if payload:
        try:
            process.stdin.write(payload + "\n")
            process.stdin.flush()
        except BrokenPipeError:
            # acontece se o processo fecha rapido demais
            pass

    process.stdin.close()


def render_report(result: RunResult, limits: Limits) -> str:
    # monta o texto final que vai aparecer no log da interface
    lines = [
        "=== RELATORIO DA EXECUCAO ===",
        f"Comando: {result.command_display}",
        f"Motivo do encerramento: {result.reason}",
        f"Codigo de saida: {result.exit_code}",
        f"Tempo de relogio: {format_seconds(result.wall_time_seconds)}",
        f"CPU usuario: {format_seconds(result.metrics.user_cpu_seconds)}",
        f"CPU sistema: {format_seconds(result.metrics.system_cpu_seconds)}",
        (
            f"CPU total: {format_seconds(result.metrics.total_cpu_seconds)}"
            f" / quota {format_seconds(limits.cpu_quota_seconds)}"
        ),
        (
            f"Pico de memoria: {format_bytes(result.metrics.peak_memory_bytes)}"
            f" / limite "
            f"{format_bytes(limits.max_memory_bytes) if limits.max_memory_bytes else 'sem limite'}"
        ),
    ]

    if result.stdout_tail:
        lines.append("")
        lines.append("Ultimas linhas capturadas de STDOUT:")
        lines.extend(f"  {line}" for line in result.stdout_tail)

    if result.stderr_tail:
        lines.append("")
        lines.append("Ultimas linhas capturadas de STDERR:")
        lines.extend(f"  {line}" for line in result.stderr_tail)

    lines.append("=== FIM DO RELATORIO ===")
    return "\n".join(lines)


def run_managed_process(
    command: list[str],
    limits: Limits,
    ui_queue: queue.Queue[tuple[str, object]],
    external_stop_event: threading.Event | None = None,
) -> RunResult:
    # deques guardam so o final da saida. ajuda no relatorio e nao pesa
    stdout_tail: deque[str] = deque(maxlen=CAPTURED_LINES_LIMIT)
    stderr_tail: deque[str] = deque(maxlen=CAPTURED_LINES_LIMIT)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except FileNotFoundError:
        raise RuntimeError("Nao foi possivel localizar o executavel informado.")
    except OSError as exc:
        raise RuntimeError(f"Falha ao iniciar o processo: {exc}") from exc

    start_time = monotonic_seconds()
    probe = build_process_probe(process.pid)
    timeout_events: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()

    # aviso a interface sobre o pid so por transparencia
    ui_queue.put(("status", f"Processo iniciado com PID {process.pid}"))

    timeout_thread = threading.Thread(
        target=timeout_monitor,
        args=(limits.timeout_seconds, stop_event, timeout_events),
        daemon=True,
        name="timeout-monitor",
    )
    timeout_thread.start()

    # duas threads simples so pra leitura de saida e erro
    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, "STDOUT", stdout_tail, ui_queue),
        daemon=True,
        name="stdout-reader",
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, "STDERR", stderr_tail, ui_queue),
        daemon=True,
        name="stderr-reader",
    )
    stdout_thread.start()
    stderr_thread.start()

    send_optional_stdin(process, limits.stdin_payload)

    reason = "finished"
    last_metrics = Metrics()

    while True:
        # aqui fica o loop principal de vigilancia
        last_metrics = probe.snapshot()

        if (
            limits.max_memory_bytes is not None
            and last_metrics.peak_memory_bytes > limits.max_memory_bytes
        ):
            reason = "memory_limit_exceeded"
            ui_queue.put(("status", "Evento detectado: memory_limit_exceeded"))
            terminate_process(process, probe)
            break

        if last_metrics.total_cpu_seconds > limits.cpu_quota_seconds:
            reason = "cpu_quota_exceeded"
            ui_queue.put(("status", "Evento detectado: cpu_quota_exceeded"))
            terminate_process(process, probe)
            break

        try:
            timeout_events.get_nowait()
            reason = "timeout_expired"
            ui_queue.put(("status", "Evento detectado: timeout_expired"))
            terminate_process(process, probe)
            break
        except queue.Empty:
            pass

        if external_stop_event is not None and external_stop_event.is_set():
            reason = "stopped_by_user"
            ui_queue.put(("status", "Evento detectado: stopped_by_user"))
            terminate_process(process, probe)
            break

        if process.poll() is not None:
            break

        time.sleep(POLL_INTERVAL_SECONDS)

    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        terminate_process(process, probe)

    # avisa a thread de timeout pra nao disparar atrasado
    stop_event.set()
    timeout_thread.join(timeout=1)
    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)

    final_metrics = probe.snapshot()
    probe.close()

    if final_metrics.total_cpu_seconds >= last_metrics.total_cpu_seconds:
        last_metrics = final_metrics

    return RunResult(
        command_display=subprocess.list2cmdline(command),
        exit_code=process.returncode,
        reason=reason,
        wall_time_seconds=monotonic_seconds() - start_time,
        metrics=last_metrics,
        stdout_tail=list(stdout_tail),
        stderr_tail=list(stderr_tail),
    )


class FMSGuiApp:
    # classe principal da interface
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FMS - Monitor de Processos")
        self.root.geometry("980x720")
        self.root.minsize(900, 650)

        # fila pra conversa entre thread do processo e thread da tela
        self.ui_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event: threading.Event | None = None

        # valores iniciais so pra facilitar teste rapido
        self.binary_var = tk.StringVar(value="python")
        self.args_var = tk.StringVar(value="")
        self.cpu_var = tk.StringVar(value="10")
        self.timeout_var = tk.StringVar(value="")
        self.memory_var = tk.StringVar(value="")
        self.stdin_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Pronto para executar.")

        self.build_layout()

        # fica conferindo a fila de tempos em tempos, ajustar se quiser mais liso
        self.root.after(100, self.process_ui_queue)

    def build_layout(self) -> None:
        # container geral
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        form = ttk.LabelFrame(container, text="Parametros da execucao", padding=12)
        form.pack(fill="x")

        ttk.Label(form, text="Binario / executavel").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.binary_var, width=72).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        ttk.Button(form, text="Selecionar", command=self.select_binary).grid(
            row=1,
            column=1,
            sticky="ew",
        )

        ttk.Label(form, text="Argumentos").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(12, 0),
        )
        ttk.Entry(form, textvariable=self.args_var).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
        )

        numeric_frame = ttk.Frame(form)
        numeric_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        ttk.Label(numeric_frame, text="Quota CPU (s)").grid(row=0, column=0, sticky="w")
        ttk.Entry(numeric_frame, textvariable=self.cpu_var, width=16).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
        )
        ttk.Label(numeric_frame, text="Timeout (s)").grid(row=0, column=1, sticky="w")
        ttk.Entry(numeric_frame, textvariable=self.timeout_var, width=16).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 12),
        )
        ttk.Label(numeric_frame, text="Memoria maxima (MB)").grid(
            row=0,
            column=2,
            sticky="w",
        )
        ttk.Entry(numeric_frame, textvariable=self.memory_var, width=16).grid(
            row=1,
            column=2,
            sticky="w",
        )

        ttk.Label(form, text="Mensagem para stdin").grid(
            row=5,
            column=0,
            sticky="w",
            pady=(12, 0),
        )
        ttk.Entry(form, textvariable=self.stdin_var).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
        )

        buttons = ttk.Frame(container, padding=(0, 12, 0, 12))
        buttons.pack(fill="x")

        self.run_button = ttk.Button(buttons, text="Executar", command=self.start_run)
        self.run_button.pack(side="left")

        self.stop_button = ttk.Button(
            buttons,
            text="Parar processo",
            command=self.stop_run,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(8, 0))

        ttk.Button(buttons, text="Limpar log", command=self.clear_log).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Label(container, textvariable=self.status_var).pack(anchor="w")

        log_frame = ttk.LabelFrame(container, text="Saida e relatorios", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(12, 0))

        # usei Text pq eh mais facil ir jogando linhas
        self.log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 10))
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        form.columnconfigure(0, weight=1)

    def select_binary(self) -> None:
        # abre janela de escolha do executavel
        filename = filedialog.askopenfilename(title="Selecione um executavel")
        if filename:
            self.binary_var.set(filename)

    def clear_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def append_log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def parse_optional_float(self, value: str, field_name: str) -> float | None:
        # validacao bem simples dos campos numericos
        value = value.strip()
        if value == "":
            return None

        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} precisa ser numerico.") from exc

        if parsed <= 0:
            raise ValueError(f"{field_name} precisa ser maior que zero.")

        return parsed

    def parse_optional_memory(self, value: str) -> int | None:
        parsed = self.parse_optional_float(value, "Memoria maxima")
        if parsed is None:
            return None
        return int(parsed * 1024 * 1024)

    def read_limits(self) -> Limits:
        # le os campos da tela e monta o objeto de limites
        cpu_quota_seconds = self.parse_optional_float(self.cpu_var.get(), "Quota CPU")
        if cpu_quota_seconds is None:
            raise ValueError("Quota CPU e obrigatoria.")

        return Limits(
            cpu_quota_seconds=cpu_quota_seconds,
            timeout_seconds=self.parse_optional_float(self.timeout_var.get(), "Timeout"),
            max_memory_bytes=self.parse_optional_memory(self.memory_var.get()),
            stdin_payload=self.stdin_var.get().strip() or None,
        )

    def start_run(self) -> None:
        # evita duas execucoes ao mesmo tempo, depois posso polir isso
        if self.worker_thread is not None and self.worker_thread.is_alive():
            messagebox.showinfo(
                "Execucao em andamento",
                "Aguarde o processo atual terminar.",
            )
            return

        executable = self.binary_var.get().strip()
        arguments = self.args_var.get().strip()

        if not executable:
            messagebox.showerror("Entrada invalida", "Informe o binario/executavel.")
            return

        try:
            limits = self.read_limits()
            command = build_command(executable, arguments)
        except ValueError as exc:
            messagebox.showerror("Entrada invalida", str(exc))
            return

        # evento usado quando o botao parar for clicado
        self.stop_event = threading.Event()
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Executando processo monitorado...")
        self.append_log(f">>> Iniciando: {' '.join(command)}")

        # essa thread executa o processo sem travar a janela
        self.worker_thread = threading.Thread(
            target=self.run_process_worker,
            args=(command, limits, self.stop_event),
            daemon=True,
            name="fms-gui-worker",
        )
        self.worker_thread.start()

    def stop_run(self) -> None:
        # so sinaliza, quem mata mesmo eh o loop principal
        if self.stop_event is not None:
            self.stop_event.set()
            self.status_var.set("Solicitando parada do processo...")

    def run_process_worker(
        self,
        command: list[str],
        limits: Limits,
        stop_event: threading.Event,
    ) -> None:
        # thread secundaria da GUI. deixa a tela respirando
        try:
            result = run_managed_process(
                command,
                limits,
                self.ui_queue,
                external_stop_event=stop_event,
            )
            self.ui_queue.put(("result", (result, limits)))
        except Exception as exc:
            self.ui_queue.put(("error", str(exc)))

    def process_ui_queue(self) -> None:
        # tudo que mexe em widget volta pra thread da interface
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()

                if kind == "log":
                    self.append_log(str(payload))

                elif kind == "status":
                    self.status_var.set(str(payload))

                elif kind == "error":
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.status_var.set("Falha ao executar processo.")
                    self.append_log(f"ERRO: {payload}")
                    messagebox.showerror("Falha", str(payload))

                elif kind == "result":
                    result, limits = payload
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.append_log(render_report(result, limits))
                    self.append_log("")

                    if result.reason in {"cpu_quota_exceeded", "memory_limit_exceeded"}:
                        self.status_var.set("Limite critico excedido. Encerrando o FMS...")
                        self.root.after(
                            100,
                            lambda: self.close_on_critical_limit(result.reason),
                        )
                    elif result.reason == "timeout_expired":
                        self.status_var.set(
                            "Timeout expirou. O FMS segue pronto para nova execucao."
                        )
                    elif result.reason == "stopped_by_user":
                        self.status_var.set(
                            "Processo encerrado por solicitacao do usuario."
                        )
                    else:
                        self.status_var.set(
                            "Execucao concluida dentro dos limites. Pronto para nova execucao."
                        )
        except queue.Empty:
            pass

        # corrgir se eu quiser resposta mais rapida
        self.root.after(100, self.process_ui_queue)

    def close_on_critical_limit(self, reason: str) -> None:
        # pelo enunciado, se estourar cpu ou memoria o FMS todo deve encerrar
        reason_text = {
            "cpu_quota_exceeded": "A quota de CPU foi excedida.",
            "memory_limit_exceeded": "O limite de memoria foi excedido.",
        }.get(reason, "Um limite critico foi excedido.")

        messagebox.showerror(
            "FMS encerrado",
            f"{reason_text}\nO FMS sera fechado agora.",
        )
        self.root.destroy()


def main() -> int:
    # ponto de entrada da aplicacao
    root = tk.Tk()

    # tema do windows, fica mais bonitinho. ajustar depois talvez
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")

    FMSGuiApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
