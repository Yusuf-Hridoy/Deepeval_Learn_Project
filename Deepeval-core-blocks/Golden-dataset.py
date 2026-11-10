from deepeval.dataset import EvaluationDataset, Golden 

golden = Golden(

    input = "What is the capital of France?",
    expected_output = "The capital of France is Paris.",
    context=["France is a country in Europe. Its capital city is Paris, which is known for its art, culture, and history."],
)

dataset = EvaluationDataset()
dataset.add_golden(golden)

dataset.push(alias="FirstDataset")