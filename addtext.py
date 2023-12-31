# Importing the PIL library
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math
import pandas as pd
import sys
from datetime import date

from printer_config import *

# fonts
nameFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 90)
statFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 112)
textFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 33)
boldFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 33)
italFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 33)
artsFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 42)
formatFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 20)
tribesFont = ImageFont.truetype('HEAVYWEIGHT.ttf', 42)

def fetchSigilText(name):
    sdf = (pd.read_csv(sigils_url)).to_dict('split')
    text = "Unknown sigil: "+str(name)
    found = False
    # Okay so I don't know about the data structures well enough
    # to do anything other than a really bad for loop
    for i in sdf["data"]:
        if i[0]==name:
            text = i[1]
            found = True
            break
        # end if
    # end for
    if not found:
        print("Unknown sigil: "+name)
    # end if
    return text
# end def

def fetchCardByName(name):
    # I am a piece of garbage (sung in G blues scale)
    #print(pd.read_csv(cards_url))
    
    cdf = pd.read_csv(cards_url).to_dict('split')
    found = False
    n=len(cdf["data"])
    idn = 0
    try:
        for i in range(n):
            if cdf["data"][i][COLUMNS["name"]].lower()==name.lower():
                idn = i
                found = True
                break
            # end if
        # end for
    except:
        print("Wacky error occurred! Is your sheet publicly viewable?")
    if not found:
        print("Failed to find card by name: "+name)
    # end if
    return idn

def printAllCards(start=-1,end=99999,mode=0,fmt=""):
    cdf = (pd.read_csv(cards_url)).to_dict('split')
    #end = min(len(cdf["data"]),end)
    counter = 0
    if end == 99999 and start != -1:
        # specifying one card
        cardRange = [start]
    else:
        cardRange = range(max(start,0),min(len(cdf["data"]),end+1))
    # end if
    for index in cardRange:
        card = cdf["data"][index]
        print("THIS CARD: "+str(card[COLUMNS["name"]]))
        cardInfo = {
            "name": str(card[COLUMNS["name"]]),
            "temple": str(card[COLUMNS["temple"]]),
            "tier": str(card[COLUMNS["tier"]]),
            "power": card[COLUMNS["power"]],
            "health": card[COLUMNS["health"]],
            "token": str(card[COLUMNS["token"]]), # todo lol
            "flavor": str(card[COLUMNS["flavor"]]),

            "cost": [],
            "sigils": [],
            "traits": [],
            "tribes": [],

            "artist": str(card[COLUMNS["illus_credit"]]),
        }

        # Power and health
        # Not reading the X value??
        # redesign to ignore it
        if str(card[COLUMNS["power"]]) == str(math.nan):
            #print("yeah there's no power here")
            cardInfo["power"] = 0
        # end if
        if str(card[COLUMNS["health"]]) == str(math.nan):
            #print("yeah there's no health here")
            cardInfo["health"] = 0
        # end if

        # Cost (this will get complicated)
        rawCostString = str(card[COLUMNS["cost"]]).lower()
        #print("cost: "+rawCostString)
        if rawCostString != "free" and not ("nan" in rawCostString):
            typeSplit = rawCostString.split("+")
            #print(typeSplit)
            for i in range(len(typeSplit)):
                typeSplit[i] = typeSplit[i].strip()
                typeSplit[i] = typeSplit[i].split(" ")
                # ruby mox fix...
                for j in range(len(typeSplit[i])):
                    if typeSplit[i][j] == "rubies":
                        typeSplit[i][j] = "ruby"
                    # end if
                # end for
                typeSplit[i][0] = int(typeSplit[i][0])
                if typeSplit[i][1] == "shattered":
                    typeSplit[i][1] += "_"+typeSplit[i][2]
                # end if
            # end for
            #print("SPLIT BY TYPE: "+str(typeSplit))
            cardInfo["cost"] = typeSplit
        # end if

        # Sigils - reworking now
        try:
            sigilsRaw = card[COLUMNS["sigils"]].split(",")
            for i in sigilsRaw:
                i = i.strip()
                if i == "":
                    continue
                # end if
                try:
                    dumbString = i+"o"
                    cardInfo["sigils"].append(i)
                except TypeError:
                    #print("NOT A STRING")
                    integer = 1
                # end try
            # end for
        except AttributeError:
            #print("no sigils")
            integer = 1
        # end try


        # Traits
        try:
            traitsRaw = card[COLUMNS["traits"]].split(",")
            for i in traitsRaw:
                i = i.strip()
                if i == "":
                    continue
                # end if
                try:
                    dumbString = i+"o"
                    cardInfo["traits"].append(i)
                except TypeError:
                    integer = 1
                # end try
            # end for
        except AttributeError:
            integer = 1
        # end try

        # Tribes - probably fine
        try:
            dumbString = card[11]+"o"
            tribes = card[11].split(" ")
            for i in tribes:
                cardInfo["tribes"].append(i)
            # end for
        except TypeError:
            #print("NOT A STRING")
            integer = 1
        # end try
        
        print(cardInfo)
        if mode==1:
            TTSPath=cardInfo["temple"]+"/"+cardInfo["tier"]+"/"
            printCard(cardInfo,prefix="output/"+TTSPath,fmt=fmt)
        else:
            printCard(cardInfo,prefix="output/reprint/",fmt=fmt)
        counter+=1
    # end for
    print("Done! Printed "+str(counter)+" cards.")
# end def

def printCard(info,savePath="output",show=False,prefix="01x 001 ",fmt=""):
    # A new card to inscrybe.
    img = Image.new("RGBA",(112,156))
    
    # The background colors.
    bgPath = "bg/bg_"
    if info["tier"]=="Rare" or info["tier"]=="Talking":
        bgPath += "rare_"
    else:
        bgPath += "common_"
    # end if
    bgPath += info["temple"].lower()
    bgPath += ".png"

    try:
        bgImg = Image.open(bgPath)
    except FileNotFoundError:
        bgImg = Image.open("bg/zerror.png")
    img.paste(bgImg,(13,27))
    bgImg.close()

    # It needs a photo...
    try:
        artImg = Image.open("art/"+info["name"]+".png")
    except FileNotFoundError:
        print("could not find portrait: "+info["name"]+".png")
        artImg = Image.open("art/nothing lol.png")
    # end try
    img.paste(artImg,(13,27),artImg.convert("RGBA"))
    artImg.close()

    # And a proper frame to accompany it.
    framePath = "frames/frame_"
    if info["tier"]=="Talking":
        framePath += "uncommon"
    elif info["tier"]=="Side Deck":
        framePath += "common"
    else:
        framePath += info["tier"].lower()
    # end if
    framePath += "_"
    framePath += info["temple"].lower()
    framePath += ".png"
    try:
        frameImg = Image.open(framePath)
    except FileNotFoundError:
        frameImg = Image.open("frames/zerror.png")
    img.paste(frameImg,(0,0),frameImg.convert("RGBA"))
    frameImg.close()

    # Get this one pixel color.
    # a surprise tool that will help us later.
    colorSample = img.getpixel((0,0))

    # Let us begin to inscrybe it.
    I0 = ImageDraw.Draw(img)

    # First, the card's cost.
    costx = 96
    costy = 14
    costn = len(info["cost"])
    for ii in range(costn):
        i = info["cost"][ii] # i made it too lazy first time so this lets me
                            # have ii as a numeric index still
        if True: # used to check special cases but no more lol
            string = i[1]
            try:
                costImg = Image.open("cost/"+string+".png")
            except FileNotFoundError:
                try:
                    string = string[:-1]
                    costImg = Image.open("cost/"+string+".png")
                except:
                    print("Unknown cost: "+string)
                    costImg = Image.open("cost/zerror.png")
                # end try
            # end try
            w = costImg.getbbox()[2]
            h = costImg.getbbox()[3]

            try:
                threshold = COSTTHRESH[string]
            except KeyError:
                print("didn't find cost limits for "+string)
                threshold = 2
            #end try
                
            # just a few
            if i[0] < threshold:
                for j in range(i[0]):
                    img.paste(costImg,
                              ((costx-(w-1)),costy-(h//2-4)),
                              costImg.convert("RGBA")
                              )
                    costx -= (w-1)
                costx -= 2
            else:
                # many
                numberString = str(i[0])
                img.paste(costImg,
                          ((costx-(w-1)),costy-(h//2-4)),
                          costImg.convert("RGBA")
                          )
                costx -= ((w-1)+6)
                alphaPaste(img,costx,costy+1,"cost/x.png")
                costx-=6
                for j in range(len(numberString)):
                    chrj = numberString[-j-1]
                    symbolString = "cost/"+chrj+".png"
                    alphaPaste(img,costx,costy,symbolString)
                    costx -= 6
                # end for
                costx += (w-4)
            # end if
            costImg.close()
        #end if
        # I don't remember where I put the separator
        # so im just gonna do it backwards lol
        # this is to put mox gems together btw
        if costn > 1 and ii < costn-1:
            string2 = info["cost"][ii+1][1]
            #print(string2)
            if string in HAPPYGEMS and string2 in HAPPYGEMS:
                costx += 2
            #end if
        #end if
    # end for

    # Scale it up to fit.
    img = img.resize((1120,1560),resample=Image.Dither.NONE)
    I1 = ImageDraw.Draw(img)
    
    # Next, the power and health. The numbers.
    if True:
        # variable stat checker
        #print(info["traits"])
        normalPower = True
        if info["traits"] != []:
            for i in info["traits"]:
                if "Power" in i:
                    normalPower = False
                    try:
                        alphaPaste(img,110,1320,"sigils/variable/"+i.strip()+".png")
                    except FileNotFoundError:
                        print("unknown variable power: "+i)
                        shadowText(I1,170,1350,str(int(info["power"])),
                                   statFont,anchor="ma")
                    # end try
                # end if
            # end for
        # end if
        if normalPower:
            shadowText(I1,170,1350,str(int(info["power"])),statFont,anchor="ma")
        # end if
    # end if
    
    shadowText(I1,930,1358,str(int(info["health"])),statFont,anchor="ma")

    # Next, we will add the sigils.
    sigilx = 150
    sigily = 920
    conduit = False
    for isig in info["sigils"]:
        if "Conduit" in isig:
            conduit = True
        # end if
    # end for
    if conduit:
        alphaPaste(img,50,850,"conduit_large.png")
    #end if
    for isig in info["sigils"]:
        #print(isig)
        # see if this is a wacky meta sigil like cell or latcher
        if isig in METASIGILS:
            alphaPaste(img,0,sigily,isig+".png")
            sigily+=120
            continue
        #end if
        # fetch icon and paste
        try:
            sigilImg = Image.open("sigils/"+isig+".png")
        except FileNotFoundError:
            sigilImg = Image.open("sigils/zerror.png")
        img.paste(sigilImg,(sigilx,sigily),sigilImg.convert("RGBA"))

        # write name
        text = fetchSigilText(isig)
        if isig in TOKENSIGILS:
            halves = text.split("(new card)")
            text = halves[0]+'\"'+info["token"]+'\"'+halves[1]
        # end if
        try:
            textLines = text.split("\n")
        
            n = len(textLines)
            if n == 1:
                textOffset = 15
                singleLine = True
            else:
                textOffset = -5
                singleLine = False
        except AttributeError:
            textOffset = 15
            singleLine = True
            textLines[0] = "missingno"
            

        # print name
        l = I1.textlength(isig+": ",boldFont)
        I1.text((sigilx+80, sigily+textOffset),
                isig+": ",
                fill=(0,0,0),
                font=boldFont,
                anchor="la"
                )

        # print first line of sigil text
        # (might be the only line)
        I1.text((sigilx+80+l, sigily+textOffset),
                textLines[0],
                fill=(0,0,0),
                font=textFont,
                anchor="la"
                )
        # and now the rest of them
        if singleLine == False:
            # skip the first one
            for i in range(n)[1:]:
                I1.text((sigilx+80, sigily+textOffset+40*i),
                textLines[i],
                fill=(0,0,0),
                font=textFont,
                anchor="la"
                )
            sigily += (n-2)*40     
        sigily += 80
        # TODO: figure out inline italics for tribe names
    # end for
    if info["sigils"] != []:
        alphaPaste(img,150,sigily-(sigily%10),"Separator_large.png")
        sigily += 15
    # end if

    # Do let me know of any traits this card might have.
    for itrait in info["traits"]:
        textLines = fetchSigilText(itrait).split("\n")
        n = len(textLines)
        sigilx += 410
        for i in textLines:
            I1.text((sigilx,sigily),
            i,
            fill=(0,0,0),
            font=textFont,
            anchor="ma"
            )
            sigily += 35
        sigily += 5
    # end for
    if info["traits"] != []:
        sigily = (math.ceil(sigily/10))*10
        alphaPaste(img,150,sigily,"Separator_large.png")
        sigily += 15
    # end if
    
    # Now we shall say which tribes it belongs to.
    #151,1296
    tribeString = info["tier"]+" "+info["temple"]
    if info["tribes"] != []:
        tribeString+=" -"
        for i in info["tribes"]:
            tribeString += " "+i
        # end for
    # end if
    I1.text((560,1375),
            tribeString,
            fill=colorSample,
            font=tribesFont,
            anchor="ma"
            )

    # At last, grace it with a description. Something for flavor.
    if info["flavor"] != "BLANK":
        #ftext = info["flavor"]
        #print(italFont.getlength(ftext))
        
        I1.text((561,sigily),
                info["flavor"],
                fill=colorSample,
                font=italFont,
                anchor="ma"
                )
    #end if

    # Name the card.
    shadowText(I1,140,130,info["name"],nameFont)

    # Do not let us forget what this is for in the end.
    if fmt != "":
        print(fmt)
        tx,ty = FORMATPOS
        I1.text(FORMATPOS,fmt,fill=colorSample,font=formatFont,anchor="ma")
    #end if
        
    # uhhh yeah
    if show:
        img.show()
    # end if
    if info["name"]!="nan":
        filePath = prefix+info["name"]+".png"
        img.save(filePath)
    # end if

# end def

def shadowText(image,x,y,text,font,anchor="la"):
    # maximum laziness
    image.text((x+5,y+5), text, fill=(0,0,0), font=font, anchor=anchor)
# end def

def alphaPaste(image,x,y,path):
    paste = Image.open(path)
    image.paste(paste,(x,y),paste.convert("RGBA"))
    paste.close()
# end def

def textlines_even(font,text,maxw):
    words = text.strip().split(" ")
    n = len(words)
    for i in range(n):
        print("TODO LOL")
    #end for
#end def
    
def main():
    #printCard(newInfo) # use this to manually print 1
    # do printAllCards(card=79) to print just the card in row 79

    gameFormatString = FORMAT_NAME +" - "+ str(date.today())

    while True:
        a = input("print cards\n[start],[end]\n").split(",")       
        n = len(a)

        if n>0:
            if type(a[0]) == type("aa"):
                s = fetchCardByName(a[0])
            elif type(a[0]) == type(2):
                s = int(s)
            #end if

            # idk what else to try here

            if n>1:
                try:
                    e = int(a[1])-2
                except ValueError:
                    # again try name
                    e = fetchCardByName(a[1])
                # end try
            # end if
        # end if
        
        if n == 0:
            # print all
            printAllCards()
        elif n == 1:
            # print one
            printAllCards(start=s,fmt=gameFormatString)
        elif n == 2:
            # print range
            printAllCards(start=s,end=e,fmt=gameFormatString)
        elif n == 3:
            printAllCards(start=s,end=e,mode=int(a[2]),fmt=gameFormatString)
        else:
            print("too many arguments what")
        # end if
    # end while
# end def
main()



