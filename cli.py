import typer
from training import training_loop
from user_query import agent

app = typer.Typer()

@app.command()
def train(cycles: int = 1, questions_per_cycle: int = 100) -> None:
    """
    Run the training workflow for a given number of cycles.
    """
    training_loop(cycles, questions_per_cycle)

@app.command()
def ask(query: str) -> None:
    """
    Ask Knowledge Graph for Unit Conversions
    Parameters: query (str): The user query string -> eg. "convert 5 meters to centimeters"
    """
    print(agent(query))


if __name__ == "__main__":
    app()
