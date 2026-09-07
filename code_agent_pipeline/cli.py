"""
命令行入口
提供 run、setup、serve 等子命令
"""

import argparse
from pathlib import Path

from rich.console import Console

from code_agent_pipeline.config import get_config
from code_agent_pipeline.graph import compile_pipeline
from code_agent_pipeline.models import PipelineState, TaskStatus

console = Console()


def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        prog="code-agent-pipeline",
        description="基于 LangGraph+CrewAI 的全流程代码研发辅助多智能体流水线",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行流水线")
    run_parser.add_argument("requirement", help="需求描述")
    run_parser.add_argument("--context", "-c", default="", help="项目上下文")
    run_parser.add_argument("--constraint", action="append", default=[], help="约束条件")
    run_parser.add_argument("--output", "-o", default="output", help="输出目录")

    # setup 命令
    setup_parser = subparsers.add_parser("setup", help="初始化项目环境")
    setup_parser.add_argument("--rag-source", default="", help="RAG 源码目录")

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.add_argument("--host", default=None, help="服务地址")
    serve_parser.add_argument("--port", "-p", type=int, default=None, help="服务端口")
    serve_parser.add_argument("--reload", action="store_true", help="热重载")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        _run_pipeline(args)
    elif args.command == "setup":
        _run_setup(args)
    elif args.command == "serve":
        _run_server(args)


def _run_pipeline(args):
    """运行流水线"""
    console.rule("[bold blue]代码研发辅助多智能体流水线[/bold blue]")

    # 初始化状态
    state = PipelineState(
        requirement=args.requirement,
        project_context=args.context,
        constraints=args.constraint,
        output_dir=Path(args.output),
        status=TaskStatus.RUNNING,
    )

    console.print(f"\n[bold]需求:[/bold] {state.requirement}")
    if state.constraints:
        console.print(f"[bold]约束:[/bold] {', '.join(state.constraints)}")

    console.print("\n[bold green]正在编译流水线...[/bold green]")
    graph = compile_pipeline()

    console.print("\n[bold green]开始执行...[/bold green]\n")

    # 执行流水线
    result = graph.invoke(state)
    final_state = PipelineState(**result)

    # 打印结果
    console.print("\n[bold green]✓ 流水线执行完成[/bold green]")
    console.print(f"  最终阶段: {final_state.current_stage.value}")
    console.print(f"  状态: {final_state.status.value}")
    console.print(f"  迭代次数: {final_state.iteration_count}")

    if final_state.agent_messages:
        console.print("\n[bold]执行日志:[/bold]")
        for msg in final_state.agent_messages[-10:]:
            console.print(f"  [{msg['agent']}] {msg['message']}")

    if final_state.errors:
        console.print("\n[bold red]错误:[/bold red]")
        for err in final_state.errors:
            console.print(f"  {err}")

    # 保存结果
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_file = output_dir / f"result_{final_state.task_id}.json"
    result_file.write_text(
        final_state.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )
    console.print(f"\n[dim]结果已保存至: {result_file}[/dim]")


def _run_setup(args):
    """初始化环境"""
    console.rule("[bold blue]项目环境初始化[/bold blue]")

    config = get_config()

    # 创建必要目录
    dirs = [
        config.output_dir,
        config.artifacts_dir,
        Path(".cache/chroma"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"  ✓ 创建目录: {d}")

    # 初始化 RAG
    if args.rag_source:
        console.print("\n[bold]初始化 RAG 索引...[/bold]")
        from ..rag.indexer import CodeIndexer  # noqa: PLC0415

        indexer = CodeIndexer()
        count = indexer.index_directory(args.rag_source)
        console.print(f"  ✓ 索引完成，共 {count} 个文档块")
    else:
        console.print("\n[dim]跳过 RAG 索引（未指定 --rag-source）[/dim]")

    console.print("\n[bold green]✓ 环境初始化完成[/bold green]")


def _run_server(args):
    """启动 API 服务"""
    config = get_config()
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port

    console.print("\n[bold]启动 API 服务...[/bold]")
    console.print(f"  地址: http://{config.host}:{config.port}")
    console.print(f"  API 文档: http://{config.host}:{config.port}/docs")

    from code_agent_pipeline.api.main import serve  # noqa: PLC0415

    serve()


if __name__ == "__main__":
    main()
