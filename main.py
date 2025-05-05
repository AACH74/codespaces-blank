import random

def play_game():
    riddles = [
        {"question": "Я — царь зверей и у меня грива. Кто я?", "answer": "лев"},
        {"question": "У меня длинная шея, я ем листья высоких деревьев. Кто я?", "answer": "жираф"},
        {"question": "Я в полоску чёрно-белую, похож на лошадь. Кто я?", "answer": "зебра"},
        {"question": "Я самый быстрый сухопутный зверь. Кто я?", "answer": "гепард"},
        {"question": "Я самое большое наземное млекопитающее. Кто я?", "answer": "слон"},
        {"question": "У меня есть панцирь, я медленно ползаю. Кто я?", "answer": "черепаха"},
        {"question": "Я единственный летающий млекопитающий. Кто я?", "answer": "летучая мышь"},
        {"question": "Я полосатая кошка, родственница льва. Кто я?", "answer": "тигр"},
        {"question": "Я могу менять цвет кожи и у меня длинный язык. Кто я?", "answer": "хамелеон"},
        {"question": "Я морское существо с восемью щупальцами. Кто я?", "answer": "осьминог"},
    ]

    random.shuffle(riddles)
    score = 0

    print("Вам предстоит отгадать 10 загадок про животных.\n")

    for i, r in enumerate(riddles, start=1):
        print(f"Загадка {i}: {r['question']}")
        user_ans = input("Ваш ответ: ").strip().lower()
        if user_ans == r["answer"]:
            print("✅ Верно!\n")
            score += 1
        else:
            print(f"❌ Неверно. Правильный ответ: {r['answer'].capitalize()}.\n")

    print(f"Игра окончена! Ваш результат: {score} из {len(riddles)}.")

if __name__ == "__main__":
    play_game()
