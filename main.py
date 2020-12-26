#Import des librairies

import asyncio
import math
import json
import ffmpeg
import discord
import youtube_dl
from fonctions import *
from datetime import datetime, timedelta
from discord.utils import get
from discord.ext import commands, tasks

#Instanciation du bot

intents = discord.Intents.default()
intents.members = True

steve = commands.Bot(command_prefix = "ldc ", description = "Steve aux commandes de la LDC !", intents=intents)
roles = []
liste_commandes = []

#Variable

musics = {}
ytdl = youtube_dl.YoutubeDL()

#Classes

class Video :
    def __init__(self, link) :
        video = ytdl.extract_info(link, download = False)
        video_format = video["formats"][0]
        self.url = video["webpage_url"]
        self.stream_url = video_format["url"]

#Fonctions

def is_music_channel(ctx) :
    return ctx.message.channel.id == 785436963490496522

def is_cmd_channel(ctx) :
    return ctx.message.channel.id == 785436944988766228

def next_(client, queue) :
    if len(queue) > 0 :
        new_song = queue[0]
        del queue[0]
        play_(client, queue, new_song)
    else :
        asyncio.run_coroutine_threadsafe(client.disconnect(), steve.loop)

def play_(client, queue, song) :

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source = song.stream_url, before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume = 0.5)

    client.play(source, after = next)   

    print("Song playing")

def reset_contrat(week_index, date_jour) :
    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    week_resets = ldc_api['calendrier'][week_index]['resets']

    if week_resets['contrats'] == 'True' :
        return
    else :
        for contrat in ldc_api['contrats'] :
            date_debut = datetime.strptime(contrat['date_debut'], '%A %d/%m/%Y')
            date_fin = date_debut + timedelta(weeks = int(contrat['nombre_de_semaine']))

            if date_jour.strftime('%A %d/%m/%Y') == date_fin.strftime('%A %d/%m/%Y') :

                f = open('./ldc_api.json', 'r')
                ldc_api = json.load(f)
                f.close()

                contrat_index = ldc_api['contrats'].index(contrat)
                valeur_contrat = contrat['valeur']
                contrat_id = contrat['contrat_id']
                joueur_id = contrat['joueur_id']
                equipe_id = contrat['equipe_id']

                #Annulation du contrat

                api_remove_contrat(str(contrat_id))
                api_remove_joueur_from_team(str(joueur_id), str(equipe_id), valeur_contrat)

                #Suppression des rôles et changement de nickname

                guild = get(steve.guilds, id = 784476911924674581)
                equipe = guild.get_role(int(equipe_id))
                role_inscrit = get(guild.roles, name="Inscrit")
                joueur = get(guild.members, id = int(joueur_id))

                asyncio.run_coroutine_threadsafe(joueur.add_roles(role_inscrit), steve.loop)
                asyncio.run_coroutine_threadsafe(joueur.remove_roles(equipe), steve.loop)

                if joueur.id != 330789745607049216 :
                    asyncio.run_coroutine_threadsafe(joueur.edit(nick = f'{joueur.name}'), steve.loop)

                equipe_trouvee = False

                for equipe_ in ldc_api['equipes']['equipes_ligue'] :
                    if equipe_['equipe_id'] == str(equipe.id) :
                        equipe_trouvee = True
                        index_equipe = ldc_api['equipes']['equipes_ligue'].index(equipe_)

                equipe_choisie = ldc_api['equipes']['equipes_ligue'][index_equipe]
                equipe_name = equipe_choisie['nom']
                equipe_logo = equipe_choisie['logo']
                equipe_color = equipe_choisie['color']

                file = discord.File(f"./Sources/Images/Logos/{equipe_logo}")
                embed = discord.Embed(title = "❌ __***Fin de contrat***__ ❌", color=int(equipe_color, base = 16))
                embed.set_thumbnail(url = f"attachment://{equipe_logo}")
                embed.add_field(name = f"{joueur.name}", value = f"achève contrat avec *{equipe_name}* !", inline=False)

                asyncio.run_coroutine_threadsafe(joueur.send(f"❌ Vous achèvez votre contrat avec **{equipe.name}** ❌!"), steve.loop)
                asyncio.run_coroutine_threadsafe(steve.get_channel(784476911924674584).send(file = file, embed = embed), steve.loop)

        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['calendrier'][week_index]['resets']['contrats'] = 'True'

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

def avertir_matchs(week_index) :
    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    week_resets = ldc_api['calendrier'][week_index]['resets']
    week = ldc_api['calendrier'][week_index]

    if week_resets['matchs'] == 'True' :
        return
    else :
        file = discord.File(f"./Sources/Images/Logos/cup_logo4.png")
        embed = discord.Embed(title = "📣 __***Annonce de la Semaine " + str(week['week']) + "***__ 📣", color=0xff7b00)
        embed.set_thumbnail(url = f"attachment://cup_logo4.png")
        embed.add_field(name = "__Map Pool__", value = week['map_pool'][0] + "\n" + week['map_pool'][1] + "\n" + week['map_pool'][2] + "\n" + week['map_pool'][3], inline=False)

        numero_match = 1

        for match in ldc_api['calendrier'][week_index]['matchs']['a_prevoir'] :
            for equipe in ldc_api['equipes']['equipes_ligue'] :
                if str(equipe['equipe_id']) == str(match['id_A']) : 
                    equipeA_index = ldc_api['equipes']['equipes_ligue'].index(equipe)
                if str(equipe['equipe_id']) == str(match['id_B']) :
                    equipeB_index = ldc_api['equipes']['equipes_ligue'].index(equipe)
            equipeA = ldc_api['equipes']['equipes_ligue'][equipeA_index]
            equipeB = ldc_api['equipes']['equipes_ligue'][equipeB_index]

            if equipeA['manager_id'] != "0" :
                managerA = get(steve.get_all_members(), id = int(equipeA['manager_id']))
            else :
                print("Manager non-attribué")
                return
            if equipeB['manager_id'] != "0" :
                managerB = get(steve.get_all_members(), id = int(equipeB['manager_id']))
            else :
                print("Manager non-attribué")
                return

            file_A = discord.File("./Sources/Images/Logos/" + equipeA['logo'])
            file_B = discord.File("./Sources/Images/Logos/" + equipeB['logo'])
            embed_A = discord.Embed(title = "📣 __***Annonce de la Semaine " + str(week['week']) + "***__ 📣", color=int(equipeA['color'], base = 16))
            embed_B = discord.Embed(title = "📣 __***Annonce de la Semaine " + str(week['week']) + "***__ 📣", color=int(equipeB['color'], base = 16))
            embed_A.set_thumbnail(url = "attachment://" + equipeA['logo'])
            embed_B.set_thumbnail(url = "attachment://" + equipeB['logo'])
            embed_A.add_field(name = "__Map Pool__", value = week['map_pool'][0] + "\n" + week['map_pool'][1] + "\n" + week['map_pool'][2] + "\n" + week['map_pool'][3], inline=False)
            embed_B.add_field(name = "__Map Pool__", value = week['map_pool'][0] + "\n" + week['map_pool'][1] + "\n" + week['map_pool'][2] + "\n" + week['map_pool'][3], inline=False)
            embed_A.add_field(name = "__Adversaire__", value = equipeB['nom'], inline=False)
            embed_B.add_field(name = "__Adversaire__", value = equipeA['nom'], inline=False)
            embed_A.add_field(name = "__Manager__", value = managerA.name, inline=True)
            embed_B.add_field(name = "__Manager__", value = managerB.name, inline=True)

            asyncio.run_coroutine_threadsafe(managerA.send(file = file_A, embed = embed_A), steve.loop)
            asyncio.run_coroutine_threadsafe(managerB.send(file = file_B, embed = embed_B), steve.loop)

            embed.add_field(name = "__Match " + str(numero_match) + "__", value = equipeA['nom'] + " VS " + equipeB['nom'], inline = False)

            numero_match += 1
        asyncio.run_coroutine_threadsafe(steve.get_channel(784476911924674584).send(file = file, embed = embed), steve.loop)

        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['calendrier'][week_index]['resets']['matchs'] = 'True'

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

#Events

@tasks.loop(minutes = 1)
async def check_date():
    date_debut = datetime.now()
    jour = datetime.now().strftime('%A')
    heure = datetime.now().strftime('%H:%M')

    f = open('ldc_api.json',)
    ldc_api = json.load(f)
    f.close()

    #Check de la semaine

    if jour == 'Tuesday' :
        date_debut -= timedelta(days=1)
    elif jour == 'Wednesday' :
        date_debut -= timedelta(days=2)
    elif jour == 'Thursday' :
        date_debut -= timedelta(days=3)
    elif jour == 'Friday' :
        date_debut -= timedelta(days=4)
    elif jour == 'Saturday' :
        date_debut -= timedelta(days=5)
    elif jour == 'Sunday' :
        date_debut -= timedelta(days=6)

    week_found = False

    for week in ldc_api['calendrier'] :
        if week['date_debut'] == date_debut.strftime('%A %d/%m/%Y') :
            week_found = True
            week_index = ldc_api['calendrier'].index(week)
    
    if week_found == False :
        return
    
    if jour == 'Tuesday' and heure == '23:28' :
        #reset_contrat(week_index, date_debut)
        avertir_matchs(week_index)

    for match in ldc_api['calendrier'][week_index]['matchs']['prevus'] :
        
        match_jour = (datetime.strptime(match['date'], '%A %d/%m/%Y %H:%M')).strftime('%A')
        match_heure = datetime.strptime(match['date'], '%A %d/%m/%Y %H:%M')
        match_heure_minus = (match_heure - timedelta(hours=1)).strftime('%H:%M')

        if jour == match_jour and heure == match_heure_minus :
            print('1 heure avant le match')

@steve.event
async def on_ready() :
    check_date.start()
    print("Steve opérationnel !")

@steve.event
async def on_message(message) :
    if message.author == steve.user :
        return
    await steve.process_commands(message)

@steve.event
async def on_member_join(member) :
    role_nouveau = member.guild.roles[1]
    await member.add_roles(role_nouveau)

@steve.event
async def on_command_error(ctx, error) :

    if isinstance(error, commands.CommandNotFound) :
        await ctx.message.author.send("⚠️ La commande n'existe pas ! ⚠️")
    elif isinstance(error, commands.MissingRequiredArgument) :
        await ctx.message.author.send("⚠️ Il manque un argument dans ta commande ! ⚠️")
    elif isinstance(error, commands.MissingRole) :
        await ctx.message.author.send("⚠️ Tu n'as pas les permissions pour lancer cette commande ! ⚠️")
    elif isinstance(error, commands.CheckFailure) :
        await ctx.message.author.send("⚠️ Vous ne pouvez pas lancer cette commande dans ce channel ! ⚠️")
    else :
        print(error)
        await ctx.message.author.send("⚠️ ERREUR ! ⚠️")

#Commandes

@steve.command()
@commands.check(is_cmd_channel)
async def membres(ctx) :
    await ctx.message.delete()
    server = ctx.guild
    await ctx.send(f"Il y a actuellement **{server.member_count} membres** sur le serveur !")

@steve.command()
@commands.check(is_music_channel)
async def next(ctx) :
    client = ctx.guild.voice_client
    next_(client, musics)

@steve.command()
@commands.check(is_music_channel)
async def stop(ctx) :
    client = ctx.guild.voice_client
    await client.disconnect()
    musics[ctx.guild] = []

@steve.command()
@commands.check(is_music_channel)
async def resume(ctx) :
    client = ctx.guild.voice_client
    if client.is_paused() :
        client.resume()

@steve.command()
@commands.check(is_music_channel)
async def pause(ctx) :
    client = ctx.guild.voice_client
    if not client.is_paused() :
        client.pause()

@steve.command()
@commands.check(is_music_channel)
async def skip(ctx) :
    client = ctx.guild.voice_client
    client.stop()

@steve.command()
@commands.has_role('Modérateur')
@commands.check(is_music_channel)
async def play(ctx, url) :

    author = ctx.message.author
    client = ctx.guild.voice_client

    if author.voice :
        channel = ctx.author.voice.channel
    else :
        await author.send("⚠️ Tu n'es pas connecté à un channel vocal ! ⚠️")
        return

    video = Video(url)

    if client and client.channel :

        video = Video(url)
        musics[ctx.guild].append(video)

    else :

        musics[ctx.guild] = []
        client = await channel.connect()
        await ctx.send(f"**Lancement de ** {video.url} par **{author.name}**")

    play_(client, musics[ctx.guild], video)

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def nettoyer(ctx, nombre : int) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification si l'auteur est modérateur

    #role_moderateur = ctx.guild.roles[6]
    #a_role_moderateur = False

    #for role in author.roles :
    #    if role == role_moderateur :
    #        a_role_moderateur = True

    #if a_role_moderateur == False :
    #    await author.send("⚠️ Tu n'as pas les droits pour effectuer cette commande ! ⚠️")
    #    return

    messages = await ctx.channel.history(limit = nombre).flatten()

    for message in messages :
        await message.delete()

@steve.command()
@commands.check(is_cmd_channel)
async def inscription(ctx) :
    author = ctx.message.author
    await ctx.message.delete()

    def check_message(message) :
        return message.author == ctx.message.author

    #Vérification si l'auteur est déjà inscrit

    role_nouveau = ctx.guild.roles[1]
    role_inscrit = ctx.guild.roles[2]

    for role in author.roles :
        if role == role_inscrit :
            await author.send("⚠️ Tu es déjà inscrit ! ⚠️")
            return
    await author.send("** 🏆 INSCRIPTION LOCKDOWN CUP 🏆 **")
    
    #Demande du pseudo

    pseudo_correct = False

    while pseudo_correct == False :

        await author.send("❓ Quel est ton pseudo in-game ? ❓")
        try :
            message_pseudo = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        pseudo = message_pseudo.content

        if pseudo != "" :
            pseudo_correct = True
        else :
            await author.send("⚠️ Ton pseudo est incorrect ! ⚠️")

    #Demande du btag

    btag_correct = False

    while btag_correct == False :

        await author.send("❓ Quel est ton battletag ? ❓")
        try :
            message_btag = await steve.wait_for("message", timeout = 40, check = check_message)
        
        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return
        
        btag = message_btag.content

        if btag != "" :
            btag_correct = True
        else :
            await author.send("⚠️ Ton battletag est incorrect ! ⚠️")

    #Demande de la côte actuelle

    cote_actuelle_correcte = False

    while cote_actuelle_correcte == False :

        await author.send("❓ Quel est ta côte actuelle **sur ton rôle principal** ? ❓")
        try :
            message_cote_actuelle = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        cote_actuelle = int(message_cote_actuelle.content)

        if cote_actuelle >= 1500 and cote_actuelle <= 4700 :
            cote_actuelle_correcte = True
        else :
            await author.send("⚠️ Ta côte actuelle est incorrecte ! ⚠️")

    #Demande du peak de côte

    cote_peak_correcte = False

    while cote_peak_correcte == False :

        await author.send("❓ Quel est ton pic de carrière **tous rôles confondus, toutes saisons confondues, tous comptes confondus** ? ❓")
        try :
            message_cote_peak = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return
        
        cote_peak = int(message_cote_peak.content)

        if cote_peak >= 1500 and cote_peak <= 4700 :
            if cote_peak >= cote_actuelle :
                cote_peak_correcte = True
            else :
                await author.send("⚠️ Ton pic de carrière est inférieur à ta côte actuelle ! ⚠️")
        else :
            await author.send("⚠️ Ton pic de carrière est incorrect ! ⚠️")

    #Demande du rôle

    message_roles = await author.send("❓ Quel est **ton rôle principal** ? *(Tank, Dps, Heal ou Flex)* ❓")
    await message_roles.add_reaction("🛡️")
    await message_roles.add_reaction("⚔️")
    await message_roles.add_reaction("💊")
    await message_roles.add_reaction("♻️")

    def check_reaction(reaction, user) :
        return user == ctx.message.author and message_roles.id == reaction.message.id and (str(reaction.emoji) == "🛡️" or str(reaction.emoji) == "⚔️" or str(reaction.emoji) == "💊" or str(reaction.emoji) == "♻️")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction)

    except :
        await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
        return

    if reaction.emoji == "🛡️" :
        role = 'Tank'
    elif reaction.emoji == "⚔️" :
        role = 'Dps'
    elif reaction.emoji == "💊" :
        role = 'Heal'
    elif reaction.emoji == "♻️" :
        role = 'Flex'

    #Demande des meilleurs picks

    picks_corrects = 0

    while picks_corrects < 3 :

        await author.send("❓ Quels sont tes **3 meilleurs picks** (tous rôles confondus) ? ❓")
        await author.send("```\npick1,pick2,pick3\n```")
        try :
            message_picks = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        picks = []
        picks.extend(message_picks.content.split(","))

        for pick in picks :
            if pick != "" :
                picks_corrects += 1
            else :
                await author.send("⚠️ Un de tes picks est incorrect ! ⚠️")
                picks_corrects = 0

    #Obtention du moment d'inscription

    date_inscription = datetime.now().strftime('%d/%m/%Y %H:%M')

    #Inscription du joueur dans le fichier de données

    api_push_joueur(pseudo, author.id, str(user), btag, cote_actuelle, cote_peak, calculerValeur(cote_actuelle, cote_peak), role, picks, date_inscription, date_inscription, 0)

    #Attribution du rôle

    await author.remove_roles(role_nouveau)
    await author.add_roles(role_inscrit)

    #Confirmation

    await author.send("✅ Vous avez bien été enregistré comme agent libre dans la LockDown Cup ! ✅\nPensez à poser votre candidature en CV dans le channel dédié pour augmenter vos chances de vous faire recruter !")

@steve.command()
@commands.check(is_cmd_channel)
async def resignation(ctx, joueurUser : discord.User) :
    author = ctx.message.author
    await ctx.message.delete()

    joueur = ctx.guild.get_member(joueurUser.id)

    #Verification des droits

    a_permissions = False
    is_author = False
    est_nouveau = False

    role_moderateur = ctx.guild.roles[6]
    role_nouveau = ctx.guild.roles[1]

    if joueur == author :
        a_permissions = True
        is_author = True
    for role in author.roles :
        if role == role_moderateur :
            a_permissions = True
        if role == role_nouveau :
            est_nouveau = True

    if est_nouveau == True :
        await author.send("⚠️ Tu n'es pas inscrit à la LDC ! ⚠️")
        return
    if a_permissions == False :
        await author.send("⚠️ Tu n'as pas les droits pour lancer cette commande ! ⚠️")
        return

    #Suppression de la liste des joueurs

    api_remove_joueur(str(joueur))

    #Rétrogradation des rôles

    for role in joueur.roles :
        await joueur.remove_roles(role)

    await joueur.add_roles(role_nouveau)

    #Confirmation

    if is_author == True :
        await author.send(f"✅ Vous vous êtes bien désinscrit(e) ! ✅")
    else :
        await author.send(f"✅ **{joueur.name}** a bien été désinscrit(e) ! ✅")

@steve.command()
@commands.check(is_cmd_channel)
async def modification(ctx) :
    author = ctx.message.author
    await ctx.message.delete()

    def check_message(message) :
        return message.author == ctx.message.author

    #Vérification si l'auteur est inscrit

    role_nouveau = ctx.guild.roles[1]

    for role in author.roles :
        if role == role_nouveau :
            await author.send("⚠️ Tu n'es pas encore inscrit ! ⚠️")
            return

    #Chargement des données depuis l'API

    f = open('ldc_api.json',)
    ldc_api = json.load(f)
    f.close()
    liste_joueurs = ldc_api['joueurs']

    #Obtention du joueur dans l'API

    joueur_trouve = False

    for joueur in ldc_api['joueurs'] :
        if joueur['dtag'] == str(author) :
            joueur_index = ldc_api['joueurs'].index(joueur)
            joueur_trouve = True

    if joueur_trouve == False :
        await author.send("⚠️ Erreur : Vous n'êtes pas reconnu dans le fichier de données ! ⚠️")
        print('ERREUR : Index non-trouvé 00010 !')
        return

    await author.send("** 🏆 MODIFICATION DES INFORMATIONS PERSONNELLES 🏆 **")

    joueur = liste_joueurs[joueur_index]
    modifications_terminees = False

    while modifications_terminees == False :

        #Demande des infos à modifier

        choix_valide = False

        while choix_valide == False :

            await author.send(f"```\nVos informations personnelles :\n\n1 - Pseudo : {joueur['pseudo']}\n2 - BattleTag : {joueur['btag']}\n3 - Côtes : {joueur['cote_peak']} | {joueur['cote_actuelle']}\n4 - Rôle : {joueur['role']}\n5 - Picks : {joueur['picks'][0]} | {joueur['picks'][1]} | {joueur['picks'][2]}\n6 - Annuler\n```")
            await author.send("❓ Quelles informations souhaitez-vous modifier ? (entrez **le numéro de la ligne**) ❓")
            
            try :
                choix_message = await steve.wait_for("message", timeout = 40, check = check_message)

            except :
                await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                return

            choix = int(choix_message.content)
            if choix <= 6 and choix >= 1 :
                choix_valide = True
            else :
                await author.send("⚠️ Votre choix n'est pas correct ! ⚠️")

        #Modifier Pseudo

        if choix == 1 :

            print("choix1")

            pseudo_correct = False

            while pseudo_correct == False :

                await author.send("❓ Quel est ton pseudo in-game ? ❓")
                try :
                    message_pseudo = await steve.wait_for("message", timeout = 40, check = check_message)

                except :
                    await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                    return

                pseudo = message_pseudo.content

                if pseudo != "" :
                    pseudo_correct = True
                else :
                    await author.send("⚠️ Ton pseudo est incorrect ! ⚠️")
            
            #Inscription de la variable dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            ldc_api['joueurs'][joueur_index]['pseudo'] = pseudo
            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

        #Modifier Btag

        if choix == 2 :

            btag_correct = False

            while btag_correct == False :

                await author.send("❓ Quel est ton battletag ? ❓")
                try :
                    message_btag = await steve.wait_for("message", timeout = 40, check = check_message)
                
                except :
                    await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                    return
                
                btag = message_btag.content

                if btag != "" :
                    btag_correct = True
                else :
                    await author.send("⚠️ Ton battletag est incorrect ! ⚠️")
            
            #Inscription de la variable dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            ldc_api['joueurs'][joueur_index]['btag'] = btag
            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

        #Modifier Côtes

        if choix == 3 :

            #Demande de la côte actuelle

            cote_actuelle_correcte = False

            while cote_actuelle_correcte == False :

                await author.send("❓ Quel est ta côte actuelle **sur ton rôle principal** ? ❓")
                try :
                    message_cote_actuelle = await steve.wait_for("message", timeout = 40, check = check_message)

                except :
                    await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                    return

                cote_actuelle = int(message_cote_actuelle.content)

                if cote_actuelle >= 1500 and cote_actuelle <= 4700 :
                    cote_actuelle_correcte = True
                else :
                    await author.send("⚠️ Ta côte actuelle est incorrecte ! ⚠️")

            #Demande du peak de côte

            cote_peak_correcte = False

            while cote_peak_correcte == False :

                await author.send("❓ Quel est ton pic de carrière **tous rôles confondus, toutes saisons confondues, tous comptes confondus** ? ❓")
                try :
                    message_cote_peak = await steve.wait_for("message", timeout = 40, check = check_message)

                except :
                    await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                    return
                
                cote_peak = int(message_cote_peak.content)

                if cote_peak >= 1500 and cote_peak <= 4700 :
                    if cote_peak >= cote_actuelle :
                        cote_peak_correcte = True
                    else :
                        await author.send("⚠️ Ton pic de carrière est inférieur à ta côte actuelle ! ⚠️")
                else :
                    await author.send("⚠️ Ton pic de carrière est incorrect ! ⚠️")
            
            #Inscription de la variable dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            ldc_api['joueurs'][joueur_index]['cote_actuelle'] = cote_actuelle
            ldc_api['joueurs'][joueur_index]['cote_peak'] = cote_peak
            ldc_api['joueurs'][joueur_index]['valeur'] = calculerValeur(cote_actuelle, cote_peak)
            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

        #Modifier Rôle

        if choix == 4 :

            #Demande du rôle

            message_roles = await author.send("❓ Quel est **ton rôle principal** ? *(Tank, Dps, Heal ou Flex)* ❓")
            await message_roles.add_reaction("🛡️")
            await message_roles.add_reaction("⚔️")
            await message_roles.add_reaction("💊")
            await message_roles.add_reaction("♻️")

            def check_reaction(reaction, user) :
                return user == ctx.message.author and message_roles.id == reaction.message.id and (str(reaction.emoji) == "🛡️" or str(reaction.emoji) == "⚔️" or str(reaction.emoji) == "💊" or str(reaction.emoji) == "♻️")

            try :
                reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction)

            except :
                await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                return

            if reaction.emoji == "🛡️" :
                role = 'Tank'
            elif reaction.emoji == "⚔️" :
                role = 'Dps'
            elif reaction.emoji == "💊" :
                role = 'Heal'
            elif reaction.emoji == "♻️" :
                role = 'Flex'
            
            #Inscription de la variable dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            ldc_api['joueurs'][joueur_index]['role'] = role
            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

        #Modifier Picks

        if choix == 5 :

            #Demande des meilleurs picks

            picks_corrects = 0

            while picks_corrects < 3 :

                await author.send("❓ Quels sont tes **3 meilleurs picks** (tous rôles confondus) ? ❓")
                await author.send("```\npick1,pick2,pick3\n```")
                try :
                    message_picks = await steve.wait_for("message", timeout = 40, check = check_message)

                except :
                    await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
                    return

                picks = []
                picks.extend(message_picks.content.split(","))

                for pick in picks :
                    if pick != "" :
                        picks_corrects += 1
                    else :
                        await author.send("⚠️ Un de tes picks est incorrect ! ⚠️")
                        picks_corrects = 0

            #Inscription de la variable dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            print(ldc_api['joueurs'][joueur_index]['picks'])

            i = 0
            while i < 3 :
                ldc_api['joueurs'][joueur_index]['picks'].pop(0)
                i += 1

            print(ldc_api['joueurs'][joueur_index]['picks'])

            for pick in picks :
                ldc_api['joueurs'][joueur_index]['picks'].append(pick)

            print(ldc_api['joueurs'][joueur_index]['picks'])

            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

        #Quitter

        if choix == 6 :
            return
        
        #Update

        f = open('ldc_api.json',)
        ldc_api = json.load(f)
        f.close()
        liste_joueurs = ldc_api['joueurs']
        joueur = liste_joueurs[joueur_index]

        await author.send(f"```\nVos informations personnelles :\n\n1 - Pseudo : {joueur['pseudo']}\n2 - BattleTag : {joueur['btag']}\n3 - Côtes : {joueur['cote_peak']} | {joueur['cote_actuelle']}\n4 - Rôle : {joueur['role']}\n5 - Picks : {joueur['picks'][0]} | {joueur['picks'][1]} | {joueur['picks'][2]}\n6 - Annuler\n```")
        message_confirm = await author.send("❓ Les modifications sont-elles correctes ? ❓")

        await message_confirm.add_reaction("✔️")
        await message_confirm.add_reaction("❌")

        def check_reaction_confirm(reaction, user) :
            return user == ctx.message.author and message_confirm.id == reaction.message.id and (str(reaction.emoji) == "✔️" or str(reaction.emoji) == "❌")

        try :
            reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction_confirm)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        if reaction.emoji == "✔️" :
            await author.send("✅ Vos modifications ont bien été prises en compte ! ✅")

            #Inscription de la valeur dans l'API

            f = open('ldc_api.json', 'r')
            ldc_api = json.load(f)
            f.close()

            derniere_modification = datetime.now().strftime('%d/%m/%Y %H:%M')
            ldc_api['joueurs'][joueur_index]['derniere_modification'] = derniere_modification

            f = open('ldc_api.json', 'w')
            json.dump(ldc_api, f)
            f.close()

            modifications_terminees = True

        elif reaction.emoji == "❌" :
            pass

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def creer_equipe_ligue(ctx, equipe : discord.Role) :
    author = ctx.message.author
    await ctx.message.delete()

    def check_message(message) :
        return message.author == ctx.message.author

    #Verification validation du rôle

    role_inscrit = get(ctx.guild.roles, name="Inscrit")
    role_nouveau = get(ctx.guild.roles, name="Nouveau")
    role_moderateur = get(ctx.guild.roles, name="Modérateur")
    role_manager = get(ctx.guild.roles, name="Manager")

    if equipe == role_inscrit or equipe == role_nouveau or equipe == role_moderateur or equipe == role_manager :
        await author.send("⚠️ Ce rôle ne peut pas héberger une équipe ! ⚠️")
        return

    #Création équipes

        #Demande du nom

    nom_correct = False

    while nom_correct == False :

        await author.send("❓ Quel est le nom de la nouvelle équipe de la ligue ? ❓")

        try :
            message_pseudo = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        nom = message_pseudo.content

        if nom != "" :
            nom_correct = True
        else :
            await author.send("⚠️ Le nom entré est incorrect ! ⚠️")

    date_creation = datetime.now().strftime('%d/%m/%Y %H:%M')

    #Vérification que l'équipe n'existe pas déjà

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for equipe_ in ldc_api['equipes']['equipes_ligue'] :
        if equipe_['nom'] == nom :
            await author.send("⚠️ Une équipe est déjà inscrite sous le même nom ! ⚠️")

    #Inscription dans l'API

    api_push_equipe_ligue(nom, "", "", equipe.id, 0, 1500000, [], [], date_creation)

    #Validation 

    await author.send(f"✅ L'équipe **{nom}** a bien été inscrite ! ✅")

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def supprimer_equipe_ligue(ctx, equipe : discord.Role) :
    author = ctx.message.author
    await ctx.message.delete()

    #Vérification que l'équipe est inscrite

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    equipe_inscrite = False

    for equipe_ligue in ldc_api['equipes']['equipes_ligue'] :

        if equipe_ligue['equipe_id'] == str(equipe.id) :

            equipe_inscrite = True
            equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe_ligue)
            equipe_nom = equipe_ligue['nom']

    if equipe_inscrite == False :
        await author.send("⚠️ L'équipe n'est pas inscrite dans la ligue ! ⚠️")
        return

    #Suppression des rôles des joueurs de l'équipe

    role_equipe = ctx.guild.get_role(equipe)

    for joueur in ldc_api['equipes']['equipes_ligue'][equipe_index]['roaster'] :
        if joueur :
            membre = ctx.guild.get_member(joueur.id)
            membre.remove_roles(role_equipe)
        else :
            print('Pas de joueur dans le roaster')

    #Suppression de l'équipe

    api_remove_equipe_ligue(equipe.id)

    #Validation

    await author.send(f"✅ L'équipe **{equipe_nom}** a bien été désinscrite ! ✅")

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur' or 'Manager')
async def signer_contrat(ctx, equipe : discord.Role, joueur : discord.Member) :
    author = ctx.message.author
    await ctx.message.delete()

    def check_message(message) :
        return message.author == ctx.message.author

    #Verification validation du rôle

    role_inscrit = get(ctx.guild.roles, name="Inscrit")
    role_nouveau = get(ctx.guild.roles, name="Nouveau")
    role_moderateur = get(ctx.guild.roles, name="Modérateur")
    role_manager = get(ctx.guild.roles, name="Manager")

    if equipe == role_inscrit or equipe == role_nouveau or equipe == role_moderateur or equipe == role_manager :
        await author.send("⚠️ Ce rôle n'a pas d'équipe ! ⚠️")
        return

    #Vérification que le joueur est sur le marché

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    sur_le_marche = False

    for joueur_ in ldc_api['joueurs'] :
        if joueur_['id'] == str(joueur.id) :
            sur_le_marche = True
            joueur_valeur = joueur_['valeur']

    if sur_le_marche == False : 
        await author.send("⚠️ Ce joueur n'est pas inscrit sur le marché ! ⚠️")
        return
    
    print('test 1')

    #Vérification que le joueur est sur le marché

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    sur_le_marche = False

    for joueur_ in ldc_api['joueurs'] :
        if joueur_['id'] == str(joueur.id) :
            sur_le_marche = True

    if sur_le_marche == False : 
        await author.send("⚠️ Ce joueur n'est pas inscrit sur le marché ! ⚠️")
        return

    #Verification que le manager est de la meme équipe

    est_manager = False
    est_moderateur = False

    for role_ in author.roles :
        if role_.name == "Manager" :
            est_manager = True
        if role_.name == "Modérateur" :
            est_moderateur = True

    est_manager_bonne_equipe = False

    if est_manager == True :
        for role_ in author.roles :
            if role_.name == equipe.name :
                est_manager_bonne_equipe = True

    if est_manager_bonne_equipe == False and est_moderateur == False :
        await author.send("⚠️ Vous n'êtes pas manager de cette équipe ! ⚠️")
        return

    #Vérification qu'il n'y a pas de contrat en cours

    contrat_en_cours = False
    somme_contrats_en_cours = 0

    for contrat in ldc_api['contrats'] :
        if contrat['equipe_id'] == str(equipe.id) :
            if contrat['joueur_id'] == str(joueur.id) :
                contrat_en_cours = True
                await author.send("⚠️ Tu as déjà un contrat en cours ou en attente avec ce joueur ! ⚠️")
                return
            for joueur_marché in ldc_api['joueurs'] :
                if joueur_marché['equipe_id'] == str(equipe.id) :
                    somme_contrats_en_cours += int(joueur_marché['valeur'])

    #Vérification qu'il n'est pas dans une équipe

    equipe_trouvee = False

    for equipe_ in ldc_api['equipes']['equipes_ligue'] :
        if equipe_['equipe_id'] == str(equipe.id) :
            equipe_trouvee = True
            equipe_budget = equipe_['budget']
            index_equipe = ldc_api['equipes']['equipes_ligue'].index(equipe_)

    if equipe_trouvee == False :
        await author.send("⚠️ Aucune équipe n'a encore été créée pour ce rôle ! ⚠️")
        return

    for joueur_ in ldc_api['equipes']['equipes_ligue'][index_equipe]['roaster'] :
        if joueur_['joueur_id'] == str(joueur.id) :
            await author.send("⚠️ Ce joueur est déjà dans une équipe ! ⚠️")

    #Verification du solde de l'équipe

    if int(equipe_budget) - int(joueur_valeur) - somme_contrats_en_cours < 0 :
        await author.send("⚠️ Ce joueur n'entre pas dans votre budget (en comptant aussi vos contrats en attente) ! ⚠️")
        return

    #Demande du nombre de semaine

    nombre_correct = False

    while nombre_correct == False :

        await author.send(f"❓ Combien de **semaines de contrat** proposes-tu à {joueur.name} ? ❓")

        try :
            message_nombre = await steve.wait_for("message", timeout = 40, check = check_message)

        except :
            await author.send("⌛ Vous avez mis trop de temps a répondre, l'inscription s'est annulée ! ⌛")
            return

        nombre = message_nombre.content

        if nombre != "" and int(nombre) > 0 and int(nombre) <= 8 :
            nombre_correct = True
        else :
            await author.send("⚠️ Le nombre de semaines entré est incorrect ! ⚠️")
    

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    contrat_id = 1

    for contrat in ldc_api['contrats'] :
        if contrat :
            contrat_id = int(ldc_api['contrats'][-1]['contrat_id']) + 1

    print(contrat_id)

    api_push_contrat(contrat_id, equipe.id, joueur.id, joueur_valeur, "", nombre, "Proposition envoyee")

    #Validation 

    await author.send(f"🕓 Votre proposition de contrat est en attente de réponse ! 🕓")

    #Envoi de la proposition au joueur

    message_proposition = await joueur.send(f"❓ L'équipe {equipe.name} vous propose un contrat de {nombre} semaine(s) avec eux ! ❓")
    await message_proposition.add_reaction("❌")
    await message_proposition.add_reaction("✔️")

    def check_reaction(reaction, user) :
        return user == joueur and message_proposition.id == reaction.message.id and (str(reaction.emoji) == "❌" or str(reaction.emoji) == "✔️")

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for contrat in ldc_api['contrats'] :
        if contrat['equipe_id'] == str(equipe.id) and contrat['joueur_id'] == str(joueur.id) :
            contrat_index = ldc_api['contrats'].index(contrat)

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 7200, check = check_reaction)

    except :
        api_remove_contrat(ldc_api['contrats'][contrat_index]['contrat_id'])
        await joueur.send("⌛ Vous avez mis trop de temps a répondre, le contrat est annulé ! ⌛")
        await author.send(f"⌛ {joueur.name} n'a pas répondu à temps, le contrat est annulé ! ⌛")
        return

    if reaction.emoji == "❌" :

        #Retirer le contrat dans l'API

        api_remove_contrat(ldc_api['contrats'][contrat_index]['contrat_id'])
        await joueur.send(f"❌ Vous avez bien **refusé la proposition** de contrat avec {equipe.name} ! ❌")
        await author.send(f"❌ {joueur.name} a **refusé votre proposition** de contrat ! ❌")
        return
        
    elif reaction.emoji == "✔️" :
        
        #Modifier le contrat dans l'API

        date_debut = datetime.now()
        jour_semaine = datetime.now().strftime('%A')

        if jour_semaine == 'Tuesday' :
            date_debut -= timedelta(days=1)
        elif jour_semaine == 'Wednesday' :
            date_debut -= timedelta(days=2)
        elif jour_semaine == 'Thursday' :
            date_debut -= timedelta(days=3)
        elif jour_semaine == 'Friday' :
            date_debut -= timedelta(days=4)
        elif jour_semaine == 'Saturday' :
            date_debut -= timedelta(days=5)
        elif jour_semaine == 'Sunday' :
            date_debut -= timedelta(days=6)

        f = open('./ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        ldc_api['contrats'][contrat_index]['date_debut'] = date_debut.strftime('%A %d/%m/%Y')
        ldc_api['contrats'][contrat_index]['etat'] = "En cours"

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

        joueur_trouve = False

        for joueur_ in ldc_api['joueurs'] :
            if joueur_['id'] == str(joueur.id) :
                joueur_trouve = True
                joueur_index = ldc_api['joueurs'].index(joueur_)
                _joueur = ldc_api['joueurs'][joueur_index]

        if joueur_trouve == False :
            print('ERREUR : Index non-trouvé !')
            return

        api_push_joueur_into_team(_joueur['pseudo'], _joueur['id'], str(equipe.id), _joueur['valeur'])

        #Asignation des roles et changement de nickname

        await joueur.add_roles(equipe)
        await joueur.remove_roles(role_inscrit)
        if joueur.id != 330789745607049216 :
            await joueur.edit(nick = f'[ {equipe.name} ] {joueur.name}')

        equipe_choisie = ldc_api['equipes']['equipes_ligue'][index_equipe]
        equipe_name = equipe_choisie['nom']
        equipe_logo = equipe_choisie['logo']
        equipe_color = equipe_choisie['color']
       
        await joueur.send(f"✅ Vous avez bien **signé** votre contrat avec {equipe.name} ! ✅")
        await author.send(f"✅ {joueur.name} a **signé** votre contrat ! ✅")

        file = discord.File(f"./Sources/Images/Logos/{equipe_logo}")
        embed = discord.Embed(title = "✅ __***Signature de contrat***__ ✅", color=int(equipe_color, base = 16))
        embed.set_thumbnail(url = f"attachment://{equipe_logo}")
        embed.add_field(name = f"{joueur.name}", value = f"signe son contrat avec *{equipe_name}* !", inline=False)

        await steve.get_channel(784476911924674584).send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def annuler_contrat(ctx, joueur : discord.Member) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification qu'il n'y a pas de contrat en cours

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    contrat_en_cours = False

    for contrat_ in ldc_api['contrats'] :
        if contrat_ :
            if contrat_['joueur_id'] == str(joueur.id) :
                contrat_en_cours = True
                contrat_index = ldc_api['contrats'].index(contrat_)
                valeur_contrat = contrat_['valeur']
                contrat_id = contrat_['contrat_id']
                equipe_id = contrat_['equipe_id']

    if contrat_en_cours == False :
        await author.send(f"⚠️ {joueur.name} n'est en contrat avec aucune équipe ! ⚠️")
        return

    equipe = ctx.guild.get_role(int(equipe_id))

    #Annulation du contrat

    api_remove_contrat(str(contrat_id))

    api_remove_joueur_from_team(str(joueur.id), str(equipe_id), valeur_contrat)

    #Suppression des rôles et changement de nickname

    role_inscrit = get(joueur.guild.roles, name="Inscrit")

    await joueur.add_roles(role_inscrit)
    await joueur.remove_roles(equipe)
    if joueur.id != 330789745607049216 :
        await joueur.edit(nick = f'{joueur.name}')

    equipe_trouvee = False

    for equipe_ in ldc_api['equipes']['equipes_ligue'] :
        if equipe_['equipe_id'] == str(equipe.id) :
            equipe_trouvee = True
            index_equipe = ldc_api['equipes']['equipes_ligue'].index(equipe_)

    equipe_choisie = ldc_api['equipes']['equipes_ligue'][index_equipe]
    equipe_name = equipe_choisie['nom']
    equipe_logo = equipe_choisie['logo']
    equipe_color = equipe_choisie['color']

    file = discord.File(f"./Sources/Images/Logos/{equipe_logo}")
    embed = discord.Embed(title = "❌ __***Rupture de contrat***__ ❌", color=int(equipe_color, base = 16))
    embed.set_thumbnail(url = f"attachment://{equipe_logo}")
    embed.add_field(name = f"{joueur.name}", value = f"achève contrat avec *{equipe_name}* !", inline=False)

    await joueur.send(f"❌ Vous achèvez votre contrat avec **{equipe.name}** ❌!")
    
    await steve.get_channel(784476911924674584).send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
async def infos_joueur(ctx, joueur : discord.User) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification qu'il n'y a pas de contrat en cours

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    #Localisation du joueur

    joueur_trouvé = False

    for joueur_ in ldc_api['joueurs'] :
        if joueur_['id'] == str(joueur.id) :
            joueur_trouvé = True
            joueur_choisi = ldc_api['joueurs'][ldc_api['joueurs'].index(joueur_)]
            if int(joueur_['equipe_id']) == 0 :
                joueur_color = "0xff7b00"
                joueur_logo = "cup_logo4.png"
            else :
                for equipe_ in ldc_api['equipes']['equipes_ligue'] :
                    if joueur_['equipe_id'] == equipe_['equipe_id'] :
                        joueur_color = equipe_['color']
                        joueur_logo = equipe_['logo']

    if joueur_trouvé == False :   
        await author.send("⚠️ Le joueur recherché n'est pas inscrit ! ⚠️")
        return

    file = discord.File(f"./Sources/Images/Logos/{joueur_logo}")
    embed = discord.Embed(title = f"__***Infos : {joueur.name}***__", color=int(joueur_color, base = 16))
    embed.set_thumbnail(url = f"attachment://{joueur_logo}")
    
    embed.add_field(name = "Pseudo", value = joueur_choisi['pseudo'], inline = True)
    embed.add_field(name = "DTag", value = joueur_choisi['dtag'], inline = True)
    embed.add_field(name = "Pic de côte", value = joueur_choisi['cote_peak'], inline = True)
    embed.add_field(name = "Valeur", value = joueur_choisi['valeur'] + "$", inline = True)
    embed.add_field(name = "BTag", value = joueur_choisi['btag'], inline = True)
    embed.add_field(name = "Côte actuelle", value = joueur_choisi['cote_actuelle'], inline = True)
    embed.add_field(name = "Rôle", value = joueur_choisi['role'], inline = True)
    embed.add_field(name = "Picks", value = joueur_choisi['picks'][0] + " / " + joueur_choisi['picks'][1] + " / " + joueur_choisi['picks'][2], inline = True)
    embed.add_field(name = "Date d'inscription", value = joueur_choisi['date_inscription'], inline = True)

    await author.send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
async def infos_equipe(ctx, equipe : discord.Role) :
    await ctx.message.delete()
    author = ctx.message.author

    role_manager = get(ctx.guild.roles, name = "Manager")

    #Localisation de l'équipe

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    equipe_inscrite = False

    for equipe_ligue in ldc_api['equipes']['equipes_ligue'] :

        if equipe_ligue['equipe_id'] == str(equipe.id) :

            equipe_inscrite = True
            equipe_index = ldc_api['equipes']['equipes_ligue'].index(equipe_ligue)
            equipe_choisie = ldc_api['equipes']['equipes_ligue'][equipe_index]

    if equipe_inscrite == False :
        await author.send("⚠️ L'équipe n'est pas inscrite dans la ligue ! ⚠️")
        return

    #Check if is manager

    is_manager = False

    for role in author.roles :
        if role == role_manager :
            is_manager = True

    #Manager

    if int(equipe_choisie['manager_id']) == 0 :
        manager_nom = "Aucun"
    else :
        for member in ctx.guild.members :
            if member.id == int(equipe_choisie['manager_id']) :
                manager_nom = member.name

    file = discord.File("./Sources/Images/Logos/" + equipe_choisie['logo'])
    embed = discord.Embed(title = "__***Infos : " + equipe_choisie['nom'] + "***__", color=int(equipe_choisie['color'], base = 16))
    embed.set_thumbnail(url = "attachment://" + equipe_choisie['logo'])
    
    embed.add_field(name = "Manager", value = manager_nom, inline = True)
    embed.add_field(name = "Budget actuel", value = equipe_choisie['budget'], inline = True)
    embed.add_field(name = "Score", value = str(equipe_choisie['score']['points']) + " pts (" + str(equipe_choisie['score']['victoires']) + "|" + str(equipe_choisie['score']['egalites']) + "|" + str(equipe_choisie['score']['defaites']) + ")")
    for joueur_roaster in equipe_choisie['roaster'] :
        for joueur_marche in ldc_api['joueurs'] :
            if int(joueur_marche['id']) == int(joueur_roaster['joueur_id']) :
                if is_manager == True :
                    for contrat in ldc_api['contrats'] :
                        if joueur_marche['id'] == contrat['joueur_id'] and equipe_choisie['equipe_id'] == contrat['equipe_id'] :
                            date_debut = datetime.strptime(contrat['date_debut'], '%A %d/%m/%Y')
                            date_fin = date_debut + timedelta(weeks = int(contrat['nombre_de_semaine']))
                    embed.add_field(name = joueur_marche['pseudo'], value = joueur_marche['cote_actuelle'] + " - " + joueur_marche['role'] + "\nFin : " + date_fin.strftime('%d %B'), inline = True)
                else :
                    embed.add_field(name = joueur_marche['pseudo'], value = joueur_marche['cote_actuelle'] + " - " + joueur_marche['role'], inline = True)

    await author.send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
async def infos_marché(ctx) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification qu'il n'y a pas de contrat en cours

    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    file = discord.File("./Sources/Images/Logos/cup_logo4.png")
    embed = discord.Embed(title = "__***Marché***__", color=0xff7b00)
    embed.set_thumbnail(url = "attachment://cup_logo4.png")

    is_manager = False
    
    for role in author.roles :
        if role.name == "Manager" or role.name == "Modérateur" :
            is_manager = True        

    for joueur in ldc_api['joueurs'] :
        if int(joueur['equipe_id']) == 0 :
            if is_manager == True :
                embed.add_field(name = joueur['pseudo'], value = joueur['cote_peak'] + "/" + joueur['cote_actuelle'] + "\n" + joueur['valeur'] + "$\n" + joueur['dtag'] + "\n**" + joueur['role'] + "**\n*" + joueur['picks'][0] + "/" + joueur['picks'][1] + "/" + joueur['picks'][2] + "*")
            else :
                embed.add_field(name = joueur['pseudo'], value = joueur['cote_peak'] + "/" + joueur['cote_actuelle'] + "\n**" + joueur['role'] + "**\n*" + joueur['picks'][0] + "/" + joueur['picks'][1] + "/" + joueur['picks'][2] + "*")

    await author.send(file = file, embed = embed)

@steve.command()
@commands.has_role('Modérateur')
@commands.check(is_cmd_channel)
async def infos_calendrier(ctx) :
    await ctx.message.delete()
    author = ctx.message.author
    
    f = open('./ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    file = discord.File("./Sources/Images/Logos/cup_logo4.png")
    embed = discord.Embed(title = "__***Calendrier***__", color=0xff7b00)
    embed.set_thumbnail(url = "attachment://cup_logo4.png")

    for week in ldc_api['calendrier'] :
        match_prevus = 0
        for match in week['matchs'] :
            match_prevus += 1
        embed.add_field(name = "__Semaine " + str(week['week']) + " : " + week['type'] + "__", value = week['date_debut'] + "\n" + str(match_prevus) + " matchs prévus")

    await author.send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Manager')
async def prog_match(ctx) :
    await ctx.message.delete()
    author = ctx.message.author

    date_debut = datetime.now()
    jour = datetime.now().strftime('%A')

    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    #Check de la semaine

    if jour == 'Tuesday' :
        date_debut -= timedelta(days=1)
    elif jour == 'Wednesday' :
        date_debut -= timedelta(days=2)
    elif jour == 'Thursday' :
        date_debut -= timedelta(days=3)
    elif jour == 'Friday' :
        date_debut -= timedelta(days=4)
    elif jour == 'Saturday' :
        date_debut -= timedelta(days=5)
    elif jour == 'Sunday' :
        date_debut -= timedelta(days=6)

    week_found = False

    for week in ldc_api['calendrier'] :
        if week['date_debut'] == date_debut.strftime('%A %d/%m/%Y') :
            week_found = True
            week_number = week['week']
            week_index = ldc_api['calendrier'].index(week)
    
    if week_found == False :
        return

    #Trouvez l'équipe du manager

    role_tokyo = get(ctx.guild.roles, name="Tokyo")
    role_rio = get(ctx.guild.roles, name="Rio")

    for role in author.roles :
        if role == role_rio :
            manager_equipe_id = role_rio.id
        if role == role_tokyo :
            manager_equipe_id = role_tokyo.id

    await author.send("** ⚽ PROGRAMMATION MATCH LOCKDOWN CUP ⚽ **")

    #Verifier si le match n'est pas programmé

    for match in ldc_api['calendrier'][week_index]['matchs']['prevus'] :
        if match['id_A'] == str(manager_equipe_id) or match['id_B'] == str(manager_equipe_id) :
            pass
        else :
            return

        if match['etat'] == 'En cours' :
            await author.send("⚠️ Votre match est en cours de la programmation ! ⚠️")
            return
        elif match['etat'] == 'Programme' :
            await author.send("⚠️ Votre match est déjà programmé le " + match['date'] + " ! ⚠️")
            return

    for match in ldc_api['calendrier'][week_index]['matchs']['a_prevoir'] :
        if match['id_A'] == str(manager_equipe_id) :
            for equipe in ldc_api['equipes']['equipes_ligue'] :
                if equipe['equipe_id'] == match['id_B'] :
                    is_equipe_A = True
                    equipe_B_nom = equipe['nom']
                    equipe_adverse = equipe
                if equipe['equipe_id'] == match['id_A'] :
                    equipe_B_nom = equipe['nom']
        elif match['id_B'] == str(manager_equipe_id) :
            for equipe in ldc_api['equipes']['equipes_ligue'] :
                if equipe['equipe_id'] == match['id_A'] :
                    is_equipe_A = False
                    equipe_A_nom = equipe['nom']
                    equipe_adverse = equipe
                if equipe['equipe_id'] == match['id_B'] :
                    equipe_B_nom = equipe['nom']
        else :
            await author.send("⚠️ Vous n'avez aucun match à programmer cette semaine ! ⚠️")
            return

    #Demande du jour

    message_jour = await author.send("❓ **Quel jour proposez-vous aux " + equipe_adverse['nom'] + "** ❓\n\n🎲 - Jeudi\n🥨 - Vendredi\n⚓ - Samedi\n🤿 - Dimanche")
    await message_jour.add_reaction("🎲")
    await message_jour.add_reaction("🥨")
    await message_jour.add_reaction("⚓")
    await message_jour.add_reaction("🤿")

    def check_reaction(reaction, user) :
        return user == ctx.message.author and message_jour.id == reaction.message.id and (str(reaction.emoji) == "🤿" or str(reaction.emoji) == "⚓" or str(reaction.emoji) == "🥨" or str(reaction.emoji) == "🎲")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction)

    except :
        await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        return

    if reaction.emoji == "🎲" :
        date_programme = date_debut + timedelta(days=3)
    elif reaction.emoji == "🥨" :
        date_programme = date_debut + timedelta(days=4)
    elif reaction.emoji == "⚓" :
        date_programme = date_debut + timedelta(days=5)
    elif reaction.emoji == "🤿" :
        date_programme = date_debut + timedelta(days=6)

    #Demande de l'heure

    message_heure = await author.send("❓ **Quelle heure proposez-vous aux " + equipe_adverse['nom'] + "** ❓\n\n1️⃣ - 16h/18h\n2️⃣ - 17h/19h\n3️⃣ - 18h/20h\n4️⃣ - 19h/21h\n5️⃣ - 20h/22h\n6️⃣ - 21h/23h")
    await message_heure.add_reaction("1️⃣")
    await message_heure.add_reaction("2️⃣")
    await message_heure.add_reaction("3️⃣")
    await message_heure.add_reaction("4️⃣")
    await message_heure.add_reaction("5️⃣")
    await message_heure.add_reaction("6️⃣")

    def check_reaction_2(reaction, user) :
        return user == ctx.message.author and message_heure.id == reaction.message.id and (str(reaction.emoji) == "6️⃣" or str(reaction.emoji) == "5️⃣" or str(reaction.emoji) == "4️⃣" or str(reaction.emoji) == "3️⃣" or str(reaction.emoji) == "2️⃣" or str(reaction.emoji) == "1️⃣")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction_2)

    except :
        await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        return

    if reaction.emoji == "1️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 16:00"), '%A %d/%m/%Y %H:%M')
    elif reaction.emoji == "2️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 17:00"), '%A %d/%m/%Y %H:%M')
    elif reaction.emoji == "3️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 18:00"), '%A %d/%m/%Y %H:%M')
    elif reaction.emoji == "4️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 19:00"), '%A %d/%m/%Y %H:%M')
    elif reaction.emoji == "5️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 20:00"), '%A %d/%m/%Y %H:%M')
    elif reaction.emoji == "6️⃣" :
        date_programme = datetime.strptime((date_programme.strftime('%A %d/%m/%Y') + " 21:00"), '%A %d/%m/%Y %H:%M')

    if len(ldc_api['calendrier'][week_index]['matchs']['prevus']) == 0 :
        match_id = 0
    else :
        match_id = int(ldc_api['calendrier'][week_index]['matchs']['prevus'][-1]['match_id']) + 1

    if is_equipe_A == True :
        ldc_api['calendrier'][week_index]['matchs']['prevus'].append({
            "match_id" : str(match_id),
            "id_A" : str(manager_equipe_id),
            "id_B" : equipe_adverse['equipe_id'],
            "etat" : "En cours",
            "date" : date_programme.strftime("%A %d/%m/%Y %H:%M")
        })
    if is_equipe_A == False :
        ldc_api['calendrier'][week_index]['matchs']['prevus'].append({
            "match_id" : str(match_id),
            "id_A" : equipe_adverse['equipe_id'],
            "id_B" : str(manager_equipe_id),
            "etat" : "En cours",
            "date" : date_programme.strftime("%A %d/%m/%Y %H:%M")
        })

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

    await author.send(f"🕓 Votre proposition d'horaire de match est en attente de réponse ! 🕓")

    manager_adverse = get(steve.get_all_members(), id = int(equipe_adverse['manager_id']))

    await manager_adverse.send("** ⚽ PROGRAMMATION MATCH LOCKDOWN CUP ⚽ **")
    message_adverse = await manager_adverse.send("❓ **Les " + equipe_adverse['nom'] + " vous propose un match cette semaine " + date_programme.strftime('%A %d/%m %H:%M') + "** ❓\nCet horaire vous convient-il ?")
    await message_adverse.add_reaction("✔️")
    await message_adverse.add_reaction("❌")

    def check_reaction_3(reaction, user) :
        return user == manager_adverse and message_adverse.id == reaction.message.id and (str(reaction.emoji) == "✔️" or str(reaction.emoji) == "❌")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction_3)

    except :
        await author.send("⌛ Le manager adverse a mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        await manager_adverse.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        return

    if reaction.emoji == "❌" :
        await author.send("❌ Le manager adverse a refusé votre proposition d'horaires, proposez-en une autre ! ❌")
        await manager_adverse.send("❌ Vous avez refusé la proposition d'horaires, proposez-en une autre ! ❌")
        return
    elif reaction.emoji == "✔️" :
        await author.send("✔️ Votre match est bien programmé le " + date_programme.strftime('%A %d/%m %H:%M') + " ! ✔️")
        await manager_adverse.send("✔️ Votre match est bien programmé le " + date_programme.strftime('%A %d/%m %H:%M') + " ! ✔️")

        f = open('ldc_api.json', 'r')
        ldc_api = json.load(f)
        f.close()

        for match in ldc_api['calendrier'][week_index]['matchs']['prevus'] :
            if match['match_id'] == str(match_id) :
                index_match = ldc_api['calendrier'][week_index]['matchs']['prevus'].index(match)

        ldc_api['calendrier'][week_index]['matchs']['prevus'][int(index_match)]['etat'] = "Programme"

        f = open('ldc_api.json', 'w')
        json.dump(ldc_api, f)
        f.close()

        file = discord.File(f"./Sources/Images/Logos/cup_logo4.png")
        embed = discord.Embed(title = "⚽ __***Annonce de match Semaine " + str(week_number) + "***__ ⚽", color=0xff7b00)
        embed.set_thumbnail(url = f"attachment://cup_logo4.png")
        embed.add_field(name = f"{equipe_A_nom} VS {equipe_B_nom}", value = date_programme.strftime('%A %d/%m %H:%M'), inline=False)

        await steve.get_channel(784476911924674584).send(file = file, embed = embed)


@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def set_manager(ctx, joueur : discord.Member) :
    await ctx.message.delete()
    author = ctx.message.author

    await author.send("** 💼 MANAGER LOCKDOWN CUP 💼 **")

    #Vérification de si le joueur est déjà manager

    role_manager = get(ctx.guild.roles, name="Manager")
    role_nouveau = get(ctx.guild.roles, name="Nouveau")
    role_tokyo = get(ctx.guild.roles, name="Tokyo")
    role_rio = get(ctx.guild.roles, name="Rio")

    for role in joueur.roles :
        if role == role_manager :
            await author.send("⚠️ Le joueur est déjà manager d'une équipe ! ⚠️")
            return

    #Demande de l'équipe

    message_equipe = await author.send("❓ **De quelle équipe " + joueur.name + " devrait-il devenir le manager ?** ❓")
    await message_equipe.add_reaction("🦅")
    await message_equipe.add_reaction("💀")
    await message_equipe.add_reaction("🐻")
    await message_equipe.add_reaction("🦜")
    await message_equipe.add_reaction("🦘")
    await message_equipe.add_reaction("🌸")

    def check_reaction(reaction, user) :
        return user == ctx.message.author and message_equipe.id == reaction.message.id and (str(reaction.emoji) == "🦅" or str(reaction.emoji) == "💀" or str(reaction.emoji) == "🐻" or str(reaction.emoji) == "🦜" or str(reaction.emoji) == "🦘" or str(reaction.emoji) == "🌸")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction)

    except :
        await author.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        return

    guild = get(steve.guilds, id = 784476911924674581)

    if reaction.emoji == "🦅" :
        print('Athens Wings')
        #equipe_role = get(get(steve.guilds, id = 784476911924674581).roles, name = "Athens")
    elif reaction.emoji == "💀" :
        #equipe_role = get(steve.roles, name = "Athens")
        print('Mexico Inferno')
    elif reaction.emoji == "🐻" :
        #equipe_role = get(steve.roles, name = "Athens")
        print('Moscow Bears')
    elif reaction.emoji == "🦜" :
        equipe_role = get(guild.roles, name = "Rio")
        print('Rio Toucans')
    elif reaction.emoji == "🦘" :
        #equipe_role = get(steve.roles, name = "Athens")
        print('Sydney Punch')
    elif reaction.emoji == "🌸" :
        equipe_role = get(guild.roles, name = "Tokyo")
        print('Tokyo Bloom')

    #Vérification si l'équipe a déjà un manager

    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()
    
    for equipe in ldc_api['equipes']['equipes_ligue'] :
        if equipe['equipe_id'] == str(equipe_role.id) :
            if equipe['manager_id'] != "0" :
                await author.send("⚠️ L'équipe possède déjà un manager en fonction ! ⚠️")
                return

    #Vérification si le joueur fait parti d'une autre équipe

    is_in_another_team = True

    print(equipe_role)

    for role in joueur.roles :
        print(role)
        if role == equipe_role :
            is_in_another_team = False

    if is_in_another_team == True :
        await author.send("⚠️ Le joueur fait parti d'une autre équipe ! ⚠️")
        return
            
    #Envoi de la demande au joueur

    await author.send(f"🕓 Votre proposition de promotion est en attente de réponse ! 🕓")

    await joueur.send("** 💼 MANAGER LOCKDOWN CUP 💼 **")
    message_joueur = await joueur.send("❓ ** Il vous est proposé une promotion en tant que manager des " + equipe_role.name + "** ❓\n\nPour rappel, un manager se doit d'être responsable, mature, raisonnable et assidu quant à sa gestion de ses joueurs.\n**Acceptez-vous cette responsabilité ?**")
    await message_joueur.add_reaction("✔️")
    await message_joueur.add_reaction("❌")

    def check_reaction_2(reaction, user) :
        return user == joueur and message_joueur.id == reaction.message.id and (str(reaction.emoji) == "✔️" or str(reaction.emoji) == "❌")

    try :
        reaction, user = await steve.wait_for("reaction_add", timeout = 40, check = check_reaction_2)

    except :
        await author.send("⌛ Le joueur a mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        await joueur.send("⌛ Vous avez mis trop de temps a répondre, la procédure s'est annulée ! ⌛")
        return

    if reaction.emoji == "❌" :
        await author.send("❌ Le joueur a refusé votre proposition de promotion ! ❌")
        await joueur.send("❌ Vous avez refusé la proposition de promotion ! ❌")
        return
    elif reaction.emoji == "✔️" :
        await author.send("✔️ Le joueur a accepté la proposition de promotion ! ✔️")
        await joueur.send("✔️ Vous devenez manager des " + equipe_role.name + " ! ✔️")

    is_joueur = False

    for role in joueur.roles :
        if role == role_rio or role == role_tokyo :
            is_joueur = True

    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()
    
    for equipe in ldc_api['equipes']['equipes_ligue'] :
        if equipe['equipe_id'] == str(equipe_role.id) :
            equipe_ = equipe
            index_equipe = ldc_api['equipes']['equipes_ligue'].index(equipe)

    ldc_api['equipes']['equipes_ligue'][index_equipe]['manager_id'] = str(joueur.id)

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

    await joueur.add_roles(role_manager)

    if is_joueur == False :
        await joueur.add_roles(equipe_role)
        await joueur.remove_roles(role_nouveau)

    file = discord.File(f"./Sources/Images/Logos/" + equipe_['logo'])
    embed = discord.Embed(title = "💼 __***Promotion de Manager***__ 💼", color=int(equipe_['color'], base = 16))
    embed.set_thumbnail(url = f"attachment://" + equipe_['logo'])
    embed.add_field(name = joueur.name , value = "devient manager des " + equipe_['nom'], inline=False)

    await steve.get_channel(784476911924674584).send(file = file, embed = embed)    

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def unset_manager(ctx, joueur : discord.Member) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification de si le joueur est déjà manager

    role_manager = get(ctx.guild.roles, name="Manager")
    role_nouveau = get(ctx.guild.roles, name="Nouveau")
    role_tokyo = get(ctx.guild.roles, name="Tokyo")
    role_rio = get(ctx.guild.roles, name="Rio")

    is_manager = False

    for role in joueur.roles :
        if role == role_manager :
            is_manager = True
    
    if is_manager == False :
        await author.send("** 💼 MANAGER LOCKDOWN CUP 💼 **")
        await author.send("⚠️ Le joueur n'est manager d'aucune équipe ! ⚠️")
        return

    f = open('ldc_api.json', 'r')
    ldc_api = json.load(f)
    f.close()

    for role in joueur.roles :
        if role == role_rio or role == role_tokyo :
            equipe_role = role
    
    for equipe in ldc_api['equipes']['equipes_ligue'] :
        if equipe['equipe_id'] == str(equipe_role.id) :
            equipe_ = equipe
            index_equipe = ldc_api['equipes']['equipes_ligue'].index(equipe)

    ldc_api['equipes']['equipes_ligue'][index_equipe]['manager_id'] = "0"

    f = open('ldc_api.json', 'w')
    json.dump(ldc_api, f)
    f.close()

    await joueur.remove_roles(role_manager)

    for joueur_ in ldc_api['equipes']['equipes_ligue'][index_equipe]['roaster'] :
        if joueur_['joueur_id'] == str(joueur.id) :
            is_joueur = True

    if is_joueur == False :
        await joueur.remove_roles(equipe_role)
        await joueur.add_roles(role_nouveau)

    file = discord.File(f"./Sources/Images/Logos/" + equipe_['logo'])
    embed = discord.Embed(title = "💼 __***Destitution de Manager***__ 💼", color=int(equipe_['color'], base = 16))
    embed.set_thumbnail(url = f"attachment://" + equipe_['logo'])
    embed.add_field(name = joueur.name , value = "n'est plus manager des " + equipe_['nom'], inline=False)

    await steve.get_channel(784476911924674584).send(file = file, embed = embed)

@steve.command()
@commands.check(is_cmd_channel)
async def convocation(ctx, joueur : discord.Member) :
    await ctx.message.delete()
    author = ctx.message.author
    
    if author.voice :
        channel = steve.get_channel(790934994218123286)
        #channel = ctx.author.voice.channel
    else :
        await author.send("⚠️ Tu n'es pas connecté à un channel vocal ! ⚠️")
        return

    if joueur and joueur.voice.channel :
        if joueur.voice.channel != channel :
            await joueur.move_to(channel)
        else :
            await author.send("⚠️ Ce joueur est déjà connecté au channel vocal ! ⚠️")
            return

    else :
        await author.send("⚠️ Ce joueur n'est pas encore connecté à un channel vocal ! ⚠️")
        await joueur.send("⚠️ Vous avez été convoqué mais vous n'êtes connecté à aucun channel vocal ! ⚠️")
        return

@steve.command()
@commands.check(is_cmd_channel)
@commands.has_role('Modérateur')
async def reset_json(ctx) :
    await ctx.message.delete()
    author = ctx.message.author

    #Vérification qu'il n'y a pas de contrat en cours

    f = open('./ldc_api_vierge.json', 'r')
    ldc_api_new = json.load(f)
    f.close()

    f = open('./ldc_api.json', 'w')
    json.dump(ldc_api_new, f)
    f.close()

    await author.send(f"✅ La base de données a bien été réinitialisée ! ✅")

@steve.command()
async def commandes(ctx) :
    await ctx.message.delete()
    author = ctx.message.author

    file = discord.File("./Sources/Images/Logos/cup_logo4.png")
    embed = discord.Embed(title = "__***Liste des commandes***__", color=0xff7b00)
    embed.set_thumbnail(url = "attachment://cup_logo4.png")
    embed.add_field(name = "Inscription", value = "S'inscrire sur le marché\n```ldc inscription```", inline=False)
    embed.add_field(name = "Modification de son profil", value = "Modifier ses informations personnelles\n```ldc modification```", inline = False)
    embed.add_field(name = "Résignation", value = "Se désinscrire de la LockDown Cup\n```ldc resignation @joueur```", inline = False)
    embed.add_field(name = "Marché", value = "Afficher les joueurs actuellement sur le marché\n```ldc infos_marché```", inline=False)
    embed.add_field(name = "Infos sur un joueur", value = "Afficher les infos d'un joueur en particulier\n```ldc infos_joueur @joueur```", inline=False)
    embed.add_field(name = "Infos sur une équipe", value = "Afficher les infos d'une équipe en particulier\n```ldc infos_equipe @equipe```", inline=False)

    for role in author.roles :
        if role.name == "Tokyo" or role.name == "Rio" :
            pass
        if role.name == "Manager" :
            embed.add_field(name = "Proposition d'un contrat", value = "Proposer un contrat à un joueur dans une équipe\n```signer_contrat @equipe @joueur```", inline = False)
        if role.name == "Modérateur" :
            embed.add_field(name = "Nombre de membres", value = "Obtenir le nombre de membres sur le serveur\n```ldc membres```", inline=False)
            embed.add_field(name = "Nettoyer un channel", value = "Nettoyer le channel d'un certain nombre de messages\n```ldc nettoyer [nombre de messages]```", inline=False)
            embed.add_field(name = "Création Equipe Ligue", value = "Créer une équipe principale de la LDC\n```creer_equipe_ligue @equipe```", inline = False)
            embed.add_field(name = "Suppression Equipe Ligue", value = "Supprimer une équipe principale de la LDC\n```supprimer_equipe_ligue @equipe```", inline = False)
            embed.add_field(name = "Proposition d'un contrat", value = "Proposer un contrat à un joueur dans une équipe\n```signer_contrat @equipe @joueur```", inline = False)
            embed.add_field(name = "Annulation d'un contrat", value = "Annuler un contrat d'un joueur en cours\n```annuler_contrat @joueur```", inline = False)
            embed.add_field(name = "Reset du Json", value = "Réinitialise et efface toutes les données du Json\n```ldc reset_json```", inline=False)

    await author.send(file = file, embed = embed)

steve.run("Nzg0NDcxMDA3MjgwNzU4ODI0.X8pxjg.ZTT-6AQ2-5tYSbLLV7c-TNmkgJU")
