import re


class InputProcessor:
    @staticmethod
    def get_valid_index(options: list[str], prompt: str = "Choose an option:") -> int:
        while True:
            print("\nOptions:")
            for i, option in enumerate(options):
                print(f"[{i}] {option}")

            try:
                user_input = input(f"{prompt} (0-{len(options) - 1}): ").strip()
                index = int(user_input)

                if 0 <= index < len(options):
                    return index
                else:
                    print("Invalid selection. Please enter a number within the range.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    @staticmethod
    def get_wiki_page(prompt: str = "Enter a Wikipedia page title:") -> str:
        while True:
            user_input = input(prompt).strip()
            if user_input:
                return user_input
            print("Invalid title. Please enter a title with letters and spaces only.")

    @staticmethod
    def get_word(prompt: str = "Enter a word:") -> str:
        pattern = r"^[a-zA-Z]+$"
        while True:
            user_input = input(prompt).strip()
            if re.match(pattern, user_input):
                return user_input
            print("Invalid word. Only letters are allowed. Try again")
