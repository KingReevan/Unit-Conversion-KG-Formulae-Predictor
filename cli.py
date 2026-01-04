import typer
from user_query import agent
from utils import console, benchmark

def ask(query: str) -> None:
    """
    Ask Knowledge Graph for Unit Conversions
    Parameters: query (str): The user query string -> eg. "convert 5 meters to centimeters"
    """
    print(agent(query))


if __name__ == "__main__":
    while True:
        user_input = typer.prompt("Enter your conversion question (or type 'exit' to quit)")
        if user_input.lower() == 'exit':
            console.print("Exiting the program. Goodbye!")
            break
        with benchmark("Total Query Time"):
            ask(user_input)