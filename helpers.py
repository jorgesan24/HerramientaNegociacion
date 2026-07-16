def formatear_tiempo(segundos):

    if segundos < 60:
        return f"{segundos:.2f} s"

    minutos = int(segundos // 60)
    segundos = segundos % 60

    return f"{minutos} min {segundos:.0f} s"