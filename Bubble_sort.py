import sys
"Запустите скрипт из командной строки, передав числа как аргументы:python bubble_sort.py 5 3 8 1 2 . . ."
def bubble_sort(arr):
    "Функция для сортировки методом пузырька."
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

if __name__ == "__main__":
    # Проверяем, что переданы аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование: python script.py число1 число2 число3 ...")
        sys.exit(1)

    # Преобразуем аргументы командной строки в список чисел
    try:
        numbers = [int(arg) for arg in sys.argv[1:]]
    except ValueError:
        print("Ошибка: все аргументы должны быть числами.")
        sys.exit(1)

    # Сортируем список методом пузырька
    sorted_numbers = bubble_sort(numbers)

    # Выводим отсортированный список
    print("Отсортированный список:", sorted_numbers)