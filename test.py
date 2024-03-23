from dice_roller.DiceThrower import DiceThrower

#     elif parsed.sides == 'P':
#         sides = ['Pink'] * 35 + ['Dot'] * 30 + ['Razorback'] * 20 + ['Trotter'] * 10 + ['Snouter'] * 4 + [
#             'Leaning Jowler']

print("----- Bad Roll")
print(DiceThrower().throw('10dP'))

print("----- Standard dice")
print(DiceThrower().throw('10d6'))

print("----- Dice Modifier")
print(DiceThrower().throw('10d6+5'))
print("----- Pool Modifier")
print(DiceThrower().throw('5d6+0+10'))

print("----- Success Threshold")
print(DiceThrower().throw('5d6>=5'))
print("----- Fail Threshold")
print(DiceThrower().throw('5d6f<=5'))
print("----- Naturals (pre mod)")
print(DiceThrower().throw('10d6ns6nf1'))

print("----- Explode")
print(DiceThrower().throw('10d6x>=5'))
print("----- Explode and Compound")
print(DiceThrower().throw('10d6xx>=5'))
print("----- Explode and Penetrate")
print(DiceThrower().throw('10d6xp>=5'))
print("----- Explode, Compound and Penetrate")
print(DiceThrower().throw('10d6xxp>=5'))

print("----- Keep High")
print(DiceThrower().throw('10d6kh5'))
print("----- Keep Low")
print(DiceThrower().throw('10d6kl5'))

print("----- Reroll until fixed")
print(DiceThrower().throw('10d6r<3'))
print("----- Reroll once")
print(DiceThrower().throw('10d6r<3'))

print("----- Everything")
print(DiceThrower().throw('10d6+0>=5f<=2xxp>=5ro=1dl5+4'))

print("----- Array of INT")
print(DiceThrower().throw('5d{1,2,3}'))
print("----- Array of Neg INT")
print(DiceThrower().throw('5d{-1,-1,0,0,1,1}'))
print("----- Array of Letters")
print(DiceThrower().throw('5d{A,B,C}'))
print("----- Array of Mixed")
print(DiceThrower().throw('5d{Ace,King,Queen,Jack,10,9}'))
print("----- Array of Strings")
print(DiceThrower().throw('5d{King,Queen,Rook,Bishop,Knight,Pawn}'))

