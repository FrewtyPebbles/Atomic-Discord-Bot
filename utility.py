def rgbtoint32(rgb):
        color = 0
        for c in rgb[::-1]:
            color = (color<<8) + c
        return color