import json
import asyncio
import discord
import math

def api_push_equipe_ligue(nom, logo, color, equipe_id, manager_id, budget, roaster, subs, date_creation) :
        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['equipes']['equipes_ligue'].append({
            'nom': f'{nom}',
            'logo': f'{logo}',
            'color': f'{color}',
            'equipe_id': f'{equipe_id}',
            'manager_id': f'{manager_id}',
            'budget': f'{budget}',
            'roaster': [],
            'subs' : [],
            'date_creation' : f'{date_creation}',
            'score' : {}
        })

        for equipe in ldc_api['equipes']['equipes_ligue'] :
            if equipe['nom'] == nom :
                equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe)

        ldc_api['equipes']['equipes_ligue'][equipe_index]['score'] = {"victoires": 0, "egalites": 0, "defaites": 0, "goal_average": 0, "points": 0}

        for joueur in roaster :
            ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'].append(joueur)

        for sub in subs :
            ldc_api['equipes']['equipes_ligue'][equipe_index]['subs'].append(sub)

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

def api_remove_equipe_ligue(equipe_id) :
    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for equipe in ldc_api['equipes']['equipes_ligue'] :
        if equipe['equipe_id'] == str(equipe_id) :
            equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe)

    ldc_api['equipes']['equipes_ligue'].pop(equipe_index)

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

def api_push_joueur(pseudo, joueur_id, dtag, btag, cote_actuelle, cote_peak, valeur, role, picks, date_inscription, derniere_modification, equipe_id) :
        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['joueurs'].append({
            'pseudo': f'{pseudo}',
            'id': f'{joueur_id}',
            'dtag': f'{dtag}',
            'btag': f'{btag}',
            'cote_actuelle': f'{cote_actuelle}',
            'cote_peak': f'{cote_peak}',
            'valeur': f'{valeur}',
            'role' : f'{role}',
            'picks' : [],
            'date_inscription' : f'{date_inscription}',
            'derniere_modification' : f'{derniere_modification}',
            'equipe_id': f'{equipe_id}'
        })

        for joueur in ldc_api['joueurs'] :
            print(joueur['dtag'])
            if joueur['dtag'] == str(dtag) :
                joueur_index = ldc_api['joueurs'].index(joueur)

        for pick in picks :
            ldc_api['joueurs'][joueur_index]['picks'].append(pick)

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

def api_remove_joueur(dtag) :
    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for joueur in ldc_api['joueurs'] :
        if joueur['dtag'] == str(dtag) :
            joueur_index = ldc_api['joueurs'].index(joueur)

    ldc_api['joueurs'].pop(joueur_index)

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

def api_push_contrat(contrat_id, equipe_id, joueur_id, valeur, date_debut, nombre_de_semaine, etat) :
        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['contrats'].append({
            'contrat_id': f'{contrat_id}',
            'equipe_id': f'{equipe_id}',
            'joueur_id': f'{joueur_id}',
            'valeur': f'{valeur}',
            'date_debut': f'{date_debut}',
            'nombre_de_semaine': f'{nombre_de_semaine}',
            'etat': f'{etat}'
        })

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

def api_remove_contrat(contrat_id) :
    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for contrat in ldc_api['contrats'] :
            if contrat['contrat_id'] == contrat_id :
                contrat_index = ldc_api['contrats'].index(contrat)

    ldc_api['contrats'].pop(contrat_index)

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

def api_push_joueur_into_team(pseudo, joueur_id, equipe_id, valeur) :
        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        for equipe in ldc_api['equipes']['equipes_ligue'] :
            if equipe['equipe_id'] == equipe_id :
                equipe['budget'] = int(equipe['budget']) - int(valeur)
                equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe)

        ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'].append({
            'pseudo': f'{pseudo}',
            'joueur_id': f'{joueur_id}'
        })

        for joueur in ldc_api['joueurs'] :
            if joueur['id'] == joueur_id :
                joueur_index = ldc_api['joueurs'].index(joueur)

        ldc_api['joueurs'][joueur_index]['equipe_id'] = equipe_id

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

def api_remove_joueur_from_team(joueur_id, equipe_id, valeur) :
    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for equipe in ldc_api['equipes']['equipes_ligue'] :
        
        if equipe['equipe_id'] == equipe_id :
            equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe)

    for joueur in ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'] :
        if joueur['joueur_id'] == joueur_id :
            joueur_index = ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'].index(joueur)

    ldc_api['equipes']['equipes_ligue'][equipe_index]['budget'] = int(ldc_api['equipes']['equipes_ligue'][equipe_index]['budget']) + int(valeur)
    ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'].pop(joueur_index)

    for joueur_ in ldc_api['joueurs'] :
        if joueur_['id'] == str(joueur_id) :
            ldc_api['joueurs'][ldc_api['joueurs'].index(joueur_)]['equipe_id'] = 0

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()


def calculerValeur(cote_actuelle, cote_peak) :
    return math.trunc(round(((abs(1960-int(cote_actuelle))*0.0005)+1)*((0.6*int(cote_peak)+1.4*int(cote_actuelle))/2)*15,-2))

