# Linearize ir-data and scale to cm
def linearize_ir_data(val):
    if val > 103:
        return 0
    if val < 18:
        return 255

    r = 1/5.104*((2914/(val+5)) - 1)

    return round(r, 2)
