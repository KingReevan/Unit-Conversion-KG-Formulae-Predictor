from neo4j import GraphDatabase
from pydantic import BaseModel, field_validator, ConfigDict
from engine import invert_formula
from dotenv import load_dotenv
from extract import ExtractedUnits

load_dotenv()

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "reevantheking19$$")
)

class ConversionRelation(BaseModel):
    from_unit:str
    to_unit:str
    formula:str
    
    model_config = ConfigDict(extra='allow')

    @field_validator("from_unit", "to_unit")
    @classmethod
    def normalize_units(cls, v: str) -> str:
        return v.lower().strip()

#To Check if the unit conversion exists in the knowledge base, returns Formula or None
def lookup_conversion(units: ExtractedUnits) -> str | None:
    with driver.session() as session:
        result = session.run(
            """
            MATCH (a:Unit {name: $unit1})-[r:CONVERTS_TO]->(b:Unit {name: $unit2})
            RETURN r.formula AS formula
            """,
            unit1=units.from_unit.lower(),
            unit2=units.to_unit.lower(),
        )

        record = result.single()
        return record["formula"] if record else None


#To Store a new conversion between two units
def store_conversion(relation: ConversionRelation):
    print(relation)
    with driver.session() as session:
        # Access extra fields
        extras = relation.model_extra or {}
        props = {"formula": relation.formula, **extras}

        session.run("""
            MERGE (a:Unit {name: $unit1})
            MERGE (b:Unit {name: $unit2})
            MERGE (a)-[r:CONVERTS_TO]->(b)
            SET r += $props
        """, 
        unit1=relation.from_unit,
        unit2=relation.to_unit,
        props=props
        )
        print(f"Forward stored: {relation.from_unit} → {relation.to_unit}")


    inverse_formula_exists = lookup_conversion(ExtractedUnits(
        from_unit = relation.to_unit, 
        to_unit = relation.from_unit
    ))

    if inverse_formula_exists:
        print("Inverse formula exists already")
        return 

    try:
        inverse_formula = invert_formula(relation.formula)
    except Exception as e:
        print("Could not compute inverse automatically:", e)
        return
    
    # 4. Store inverse relation
    with driver.session() as session:
        session.run("""
            MERGE (a:Unit {name: $unit1})
            MERGE (b:Unit {name: $unit2})
            MERGE (a)-[r:CONVERTS_TO]->(b)
            SET r.formula = $inverse_formula
        """,
        unit1=relation.to_unit,
        unit2=relation.from_unit,
        inverse_formula=inverse_formula)

        print(f"Inverse stored: {relation.to_unit} → {relation.from_unit}: {inverse_formula}")
