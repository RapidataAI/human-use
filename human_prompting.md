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
