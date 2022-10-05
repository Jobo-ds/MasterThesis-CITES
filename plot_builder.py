import pycountry

def get_alpha_2_code(alpha_2):
    for co in list(pycountry.countries):
        if alpha_2 in co.alpha_2:
            return co.alpha_3
        else:
            for co in list(pycountry.historic_countries):
                if alpha_2 in co.alpha_2:
                    return co.alpha_3
    return alpha_2 + "(Not Found)"