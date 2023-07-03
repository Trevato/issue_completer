import os
import json
import openai

from dotenv import load_dotenv
from github import Github
from github import Auth
from txtai.embeddings import Embeddings


load_dotenv()

openai.api_key = os.getenv("OPENAI_ACCESS_TOKEN", "")

main_system_prompt = "You are Issue Completer. You are given a GitHub repository and your goal is to help solve issues. You have the programming capabilities of a Google Principle Engineer and stricly follow the first principles of engineering. You will be working on your own branch so feel free to make any changes you see fit but remember to focus on what the user wants. Also, only complete one issue at a time. When you have a chosen an issue to complete please finish it before moving on to another one."


class IssueCompleter:
    def __init__(
        self,
        repo,
        bot_branch,
        user_system_prompt,
    ):
        self.repo = repo
        self.bot_branch = bot_branch
        self.user_system_prompt = user_system_prompt

        self.available_functions = {
            "take_action": self.take_action,
        }

        with open("functions.json") as json_functions:
            self.functions = json.load(json_functions)

        self.messages = [
            {"role": "system", "content": main_system_prompt},
            {"role": "user", "content": self.user_system_prompt},
        ]

        self.gh_auth = Auth.Token(os.getenv("GITHUB_ACCESS_TOKEN", ""))
        self.g = Github(auth=self.gh_auth)

    def step(self):
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            temperature=0,
            messages=self.messages,
            functions=self.functions,
            function_call="auto",
        )

        response_message = response["choices"][0]["message"]  # type: ignore

        if response_message.get("function_call"):
            available_functions = self.available_functions
            function_name = response_message["function_call"]["name"]
            function_to_call = available_functions[function_name]
            function_args = json.loads(response_message["function_call"]["arguments"])
            function_response = function_to_call(**function_args)
            self.messages.append(response_message)
            self.messages.append(
                {
                    "role": "function",
                    "name": str(function_name),
                    "content": str(function_response),
                }
            )
        else:
            self.messages.append(response_message)

    def take_action(self, prompt):
        available_functions = {
            "get_open_issues": "Returns a list of open issues on the repo",
            "get_issue": "Returns more information on a specific issue",
            "get_specific_content_file": "Return the contents of a file or directory",
            "decode_content_file": "Return the actual contents of a file",
            "create_new_file": "Creates a new file",
            "update_file": "Edit an existing file",
            "delete_file": "Delete a file",
        }

        embeddings = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2"})
        embeddings.index(list(available_functions))

        return embeddings.search(prompt, 1)

from termcolor import colored


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    formatted_messages = []
    for message in messages:
        if message["role"] == "system":
            formatted_messages.append(f"system: {message['content']}\n")
        elif message["role"] == "user":
            formatted_messages.append(f"user: {message['content']}\n")
        elif message["role"] == "assistant" and message.get("function_call"):
            formatted_messages.append(f"assistant: {message['function_call']}\n")
        elif message["role"] == "assistant" and not message.get("function_call"):
            formatted_messages.append(f"assistant: {message['content']}\n")
        elif message["role"] == "function":
            formatted_messages.append(
                f"function ({message['name']}): {message['content']}\n"
            )
    for formatted_message in formatted_messages:
        print(
            colored(
                formatted_message,
                role_to_color[
                    messages[formatted_messages.index(formatted_message)]["role"]
                ],
            )
        )


if __name__ == "__main__":
    repo = input("Enter the repository name (ie. Trevato/issue_completer): ")
    bot_branch = input(
        "Enter the branch for the bot to work on (the branch must already be created): "
    )
    user_system_prompt = input(
        "Enter the user system prompt (give the bot more information on what you'd like it to work on): "
    )
    ic = IssueCompleter(
        repo=repo, bot_branch=bot_branch, user_system_prompt=user_system_prompt
    )
    while True:
        ic.step()
        pretty_print_conversation(ic.messages)
