import pytest

import app.schemas.questions as pydantic
import app.models.neo4j_model as neo

from app.routes.question import (_create_question_sync,
                                 pydantic_to_neomodel)


@pytest.mark.asyncio
async def test_pydantic_to_neomodel_fill_in():
    """
    Test if the pydantic_to_neomodel to convert the FillInTheBlankQuestion
    """
    pydantic_question = pydantic.FillInTheBlankQuestion(
        difficulty=pydantic.QuestionDifficulty.EASY,
        text="To be or not to be, ___ ___ ___ ___",
        knowledge_node_id="some_node_id",
        details=pydantic.FillInTheBlankDetails(
            expected_answer=["that", "is", "the", "question"]
        )
    )

    neomodel_instance = pydantic_to_neomodel(pydantic_question)

    assert isinstance(neomodel_instance, neo.FillInBlank)
    assert neomodel_instance.difficulty == pydantic_question.difficulty.value
    assert neomodel_instance.text == pydantic_question.text
    assert neomodel_instance.expected_answer == pydantic_question.details.expected_answer


@pytest.mark.asyncio
async def test_pydantic_to_neomodel_multiple():
    pydantic_question = pydantic.MultipleChoiceQuestion(
        difficulty=pydantic.QuestionDifficulty.EASY,
        text="What is the capital of France?",
        knowledge_node_id="some_node_id",
        details=pydantic.MultipleChoiceDetails(
            options=["London", "Paris", "Berlin", "Madrid"],
            correct_answer=1
        )
    )

    neomodel_instance = pydantic_to_neomodel(pydantic_question)

    assert isinstance(neomodel_instance, neo.MultipleChoice)
    assert neomodel_instance.difficulty == pydantic_question.difficulty.value
    assert neomodel_instance.text == pydantic_question.text
    assert neomodel_instance.options == pydantic_question.details.options
    assert neomodel_instance.correct_answer == pydantic_question.details.correct_answer


@pytest.mark.asyncio
async def test_pydantic_to_neomodel_calculation():
    pydantic_question = pydantic.CalculationQuestion(
        difficulty=pydantic.QuestionDifficulty.HARD,
        text="What is 2 + 2 * 2?",
        knowledge_node_id="some_node_id",
        details=pydantic.CalculationDetails(
            expected_answer=["6"],
            precision=0
        )
    )

    neomodel_instance = pydantic_to_neomodel(pydantic_question)

    assert isinstance(neomodel_instance, neo.Calculation)
    assert neomodel_instance.difficulty == pydantic_question.difficulty.value
    assert neomodel_instance.text == pydantic_question.text
    assert neomodel_instance.expected_answer == pydantic_question.details.expected_answer
    assert neomodel_instance.precision == pydantic_question.details.precision

