#Listes

mobs_dans_la_salle = ["Gobelin", "Triton", "Machupichou"]

#print(mobs_dans_la_salle[0])

for mob in mobs_dans_la_salle :
    pass
    #print(mob + " a perdu 2 pv")

mobs_dans_la_salle.append('Boss')
mobs_dans_la_salle.pop(0)

#Dictionnaires

gobelin = {"vie" : 12, "dgt" : 4, "CA" : 12}

gobelin['vie'] += 5

#print(gobelin['vie'])

#JSON

#f = open('./ldc_api.json', 'r')
#ldc_api = json.load(f)
#f.close()

#f = open('ldc_api.json', 'w')
#json.dump(ldc_api, f)
#f.close()

import json
import random

f = open('./sorts.json', 'r')
sorts = json.load(f)
f.close()

print(sorts)

nombre_de_dgt = random.randint(1, sorts[0]['dmg'])

print(nombre_de_dgt)

sorts.append({
    "name" : "Fleur de Régénération",
    "heal" : 2,
    "classe" : "Chaman"
})

#f = open('./sorts.json', 'w')
#json.dump(sorts, f)
#f.close()


