import asyncio
import argparse
import logging
from rich.console import Console
from core.config import Config
from generator.project import ProjectGenerator

console = Console()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("appgen")


async def main_async():
    parser = argparse.ArgumentParser(description="AI-Powered Application Generator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument("--description", help="Application description")
    parser.add_argument("--max-iterations", type=int, default=5)
    args = parser.parse_args()

    if args.config:
        Config.from_file(args.config)
    if args.output:
        Config.options.output_dir = args.output
    if args.model:
        Config.options.model = args.model

    console.rule("[bold blue]AI-Powered Application Generator")
    console.print(f"Using model: {Config.options.model}")
    console.print(f"Output directory: {Config.options.output_dir}")

    generator = ProjectGenerator()
    description = args.description or input("Enter application description: ")
    await generator.iterative_development_async(description, args.max_iterations)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
