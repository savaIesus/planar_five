def change_square_color(squares, x, y, color):
    """
    Изменяет цвет указанного квадрата.

    Параметры:
    squares: Двумерный массив квадратов.
    X (int): Индекс строки.
    Y (int): Индекс столбца.
    Color: Новый цвет квадрата.

    Возвращает:
    NONE
    """
    squares[x][y].bgcolor = color
    squares[x][y].update()
