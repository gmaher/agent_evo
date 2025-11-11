# TODO

- better system prompt around using tools
  - few shots (using available tools)
- better system prompt around building teams and agents
- full code execution environment
- output directory to run directory
- task set
- initial builder sampling

# Process

dataset

- folders 1,...,N
- each folder contains task.txt and /context

goal

- optimize agent _builder_ (AB)

process

- sample different ABs
- for each AB

  - for each Task
    - ask AB to create agent team T and tools to complete task
    - ask T to complete the task
    - run evaluation on output

- for each AB

  - calculate average score, maybe variance

- choose top K ABs

- choose subsets and combine to make new AB
- repeat loop
