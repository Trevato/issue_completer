import os
import json
import openai

from dotenv import load_dotenv
from github import Github
from github import Auth


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
            "get_open_issues": self.get_open_issues,
            "get_issue": self.get_issue,
            "get_root_directory_contents": self.get_root_directory_contents,
            "get_specific_content_file": self.get_specific_content_file,
            "decode_content_file": self.decode_content_file,
            "create_new_file": self.create_new_file,
            "update_file": self.update_file,
            "delete_file": self.delete_file,
            "clear_conversation": self.clear_conversation,
            "get_file_sha": self.get_file_sha,
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

    def get_open_issues(self):
        repo = self.g.get_repo(self.repo)
        open_issues = repo.get_issues(state="open")
        return [(issue.title, issue.number) for issue in open_issues]

    def get_issue(self, issue_number):
        repo = self.g.get_repo(self.repo)
        issue = repo.get_issue(number=issue_number)
        return str(issue)

    def get_root_directory_contents(self):
        repo = self.g.get_repo(self.repo)
        return repo.get_contents("")

    def get_specific_content_file(self, file_path):
        repo = self.g.get_repo(self.repo)
        return repo.get_contents(file_path)

    def decode_content_file(self, file_path):
        repo = self.g.get_repo(self.repo)
        return repo.get_contents(file_path).decoded_content.decode("utf-8")  # type: ignore

    def get_file_sha(self, file_path):
        repo = self.g.get_repo(self.repo)
        return repo.get_contents(file_path).sha  # type: ignore

    # TODO: change author to bot
    def create_new_file(self, file_path, commit_message, file_content):
        repo = self.g.get_repo(self.repo)
        return repo.create_file(
            file_path, commit_message, file_content, self.bot_branch
        )

    # TODO: get_contents returns either a ContentFile object or a list of them which is the reason for the type ignoring. This should be changed to be safer
    def update_file(
        self, file_path, commit_message, old_file_content, new_file_content
    ):
        repo = self.g.get_repo(self.repo)
        contents = repo.get_contents(file_path)

        # TODO: This is a hacky way to replace the old file content with the new file content. This should be changed to be safer
        new_contents = contents.decoded_content.decode("utf-8").replace(  # type: ignore
            old_file_content, new_file_content
        )
        repo.update_file(
            contents.path,  # type: ignore
            commit_message,
            new_contents,
            contents.sha,  # type: ignore
            branch=self.bot_branch,
        )

    # TODO: get_contents returns either a ContentFile object or a list of them which is the reason for the type ignoring. This should be changed to be safer
    def delete_file(self, file_path, commit_message):
        repo = self.g.get_repo(self.repo)
        contents = repo.get_contents(file_path)
        repo.delete_file(
            contents.path,  # type: ignore
            commit_message,
            contents.sha,  # type: ignore
            branch=self.bot_branch,
        )

    def clear_conversation(self):
        self.messages = [
            {"role": "system", "content": main_system_prompt},
            {"role": "user", "content": self.user_system_prompt},
        ]


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
