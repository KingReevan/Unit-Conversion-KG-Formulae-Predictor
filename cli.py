import typer
from user_query import agent

app = typer.Typer()

@app.command()
def ask(query: str) -> None:
    """
    Ask Knowledge Graph for Unit Conversions
    Parameters: query (str): The user query string -> eg. "convert 5 meters to centimeters"
    """
    print(agent(query))


if __name__ == "__main__":
    app()
