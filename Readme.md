# Issue Completer

Issue Completer is an autonomous agent designed to complete issues in a GitHub repository. Simply provide it with a repository, a branch, and a prompt, and watch as it tackles and resolves your coding challenges!

## How to use:
1. Clone the repository
2. Create a file called `.env` in the root directory and enter the following environment variables:

```
GITHUB_ACCESS_TOKEN={YOUR_GITHUB_TOKEN} # requires permissions
OPENAI_ACCESS_TOKEN={YOUR_OPENAI_TOKEN}
```

**Note:** *Access to GPT-4 is required to use Issue Completer in its current state. However, with some modifications, you can utilize another LLM.*

```
pip install -r requirements.txt
python main.py
```

Upon execution, you will be prompted to input the repository and a branch for the bot to work on. You will also provide a prompt to guide the bot more effectively.

## Philosophy
Recent advancements in Large Language Models (LLMs) have led to numerous attempts to create AI capable of coding. However, these attempts often grant the model either too much or too little freedom. The tendency of these models to hallucinate presents issues when generating code from scratch; meanwhile, AI autocomplete fails to satisfy all requirements. Issue Completer aims to bridge this gap by striking a balance between model autonomy and programmer input. Rather than creating an entire codebase from scratch or relying solely on a programmer's constant input, Issue Completer utilizes LLMs that have been trained on the entire internet, including GitHub. By treating the model like a collaborator on a project, we leverage its existing knowledge and training.

## Looking Forward
Embracing this philosophy, we strive to grant the model as much freedom as possible while maintaining a programmatic approach. The implementation consists of functions for the model to use, mirroring those available to human programmers, without taking shortcuts. This design choice takes into consideration the possibility of models developing unique perspectives on software development. While there is still much work to be done, we have released the current code to prevent over-engineering. Pull requests are appreciated, and we eagerly welcome identified issues (no pun intended!).

## Known Limitations
- Running this model can become expensive quickly. Based on our tests (see the `example_outputs` folder), the model tends to generate extensive outputs. However, as LLMs are becoming more affordable, we decided not to limit this behavior prematurely. It may be beneficial to develop a function that enables the model to comment its thoughts on the issue.
- Testing scalability is challenging. We expect potential issues with context window size when dealing with larger codebases.
- Developing an effective way to let the model edit files remains an ongoing task. While the current `replace()` method has performed well in tests, we foresee potential complications as the codebase grows.

*Undoubtedly, further issues exist, some of which may stem from the implementation itself. Nevertheless, we wanted to share our concept, as we believe it could become a highly valuable tool for developers.*
