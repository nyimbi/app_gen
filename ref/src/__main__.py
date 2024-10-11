"""Command-line interface."""
import click
import .codegen as cg 

@click.command()
@click.version_option()
@click.option(
    "-o",
    "--writedir",
    type=click.Path(exists=False, file_okay=False),
    default="./",
    help="your flask-appbuilder 'app' directory to write the files to",
)
@click.option(
    "-d", "--database", default="tt", help="The name of the database to introspect"
)
@click.option(
    "-c", "--wdatabase", default="plat", help="The name of the database to create"
)
def main() -> None:
    """Appgen."""


if __name__ == "__main__":
    main(prog_name="appgen")  # pragma: no cover
    md, insp = cg.inspect_database('postgresql:///wakala1')

