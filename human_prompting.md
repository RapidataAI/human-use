# Effective Instruction Design for Rapidata Tasks

When creating tasks for human annotators using the Rapidata API, phrasing your instructions well can significantly improve quality and consistency of the responses you receive. This guide provides best practices for designing effective instructions for your Rapidata tasks.

## Time Constraints

Each annotator session (specified in the selections) has a limited time window of 25 seconds to complete all tasks. With this in mind:

- **Be concise**: Keep instructions as brief as possible while maintaining clarity
- **Use simple language**: Avoid complex terminology or jargon
- **Focus on the essentials**: Include only what is needed to complete the task

## Language Clarity

Since Rapidata tasks are presented to a diverse audience of annotators:

- **Use accessible language**: The average person should be able to understand your instructions clearly
- **Avoid ambiguity**: Ensure there's only one way to interpret your instructions
- **Be specific**: Clearly state what you're looking for in the responses

## Question Framing

The way you frame questions significantly impacts response quality:

### Use Positive Framing
Frame questions in the positive rather than negative. Positive questions are easier to process quickly.

**Better:**
```
"Which image looks more realistic?"
```

**Avoid:**
```
"Which image looks less AI-generated?"
```

### Limit Decision Criteria
Don't overload annotators with multiple criteria in a single question.

**Better:**
```
"What animal is in the image? - rabbit/dog/cat/other"
```

**Avoid:**
```
"Does this image contain a rabbit, a dog, or a cat? - yes/no"
```

### Use Clear Response Options
Provide distinct, non-overlapping response options.

**Better:**
```
"Rate the image quality: poor/acceptable/excellent"
```

**Avoid:**
```
"Rate the image quality: bad/not good/fine/good/great"
```

## Task Sequence Considerations

When using multiple selections in a session, consider the cognitive load and time constraints:

```python
from rapidata import LabelingSelection, ValidationSelection

# Keep the total number of tasks manageable for the 25-second window
selections=[
    ValidationSelection("67cafc95bc71604b08d8aa62", 1),  # Start with one validation task (id is the validation set id)
    LabelingSelection(2)  # Follow with one labeling task
]
```

## Example Implementation

When creating a Rapidata order, implement these principles as follows:

```python
order = rapi.order.create_compare_order(
    name="Image Coherence Comparison",
    instruction="Which images has more glitches and is more likely to be AI generated?",  # Clear, positive framing
    datapoints=[["https://assets.rapidata.ai/flux-1.1-pro/33_2.jpg", 
    "https://assets.rapidata.ai/stable-diffusion-3/33_0.jpg"]],
    selections=selections  # Include the above-defined selections
)
```

## Common Task Types and Recommended Instructions

### Image Comparison Tasks

```python
# Comparing image preference
instruction="Which image do you prefer?"

# Comparing prompt adherence
instruction="Which image matches the description better?"

# Comparing image coherence
instruction="Which images has more glitches and is more likely to be AI generated?"

# Comparing two texts
instruction="Which of these sentences makes more sense?"
```

### Classification Tasks

```python
# Simple classification
instruction="What object is in the image?"

# Likert classification (add no shuffling setting)
instruction="How well does the video match the description?
answer_options=["1: Perfectly", 
                "2: Very well", 
                "3: Moderately", 
                "4: A little", 
                "5: Not at all"]
```

## Monitoring and Iteration

After launching your order, monitor the initial responses to see if annotators are understanding your instructions as intended.

You can see how the users will be presented with the task by calling the `.preview()` method on the order object:
```python
order.preview()
```

If you see that annotators are giving inconsistent or incorrect answers:

1. Pause your order
2. Review and simplify your instructions 
3. Update your selections if needed
4. Start a new order with the improved settings

This helps ensure you get high quality results from annotators.

For more information on creating and managing orders, refer to the [Rapidata API documentation](index.md) and [Understanding the Results](/understanding_the_results/) guide.
