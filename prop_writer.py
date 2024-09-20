

def pafterq(p, q):
    return f'((G ~({q}))|F(({q})& F({p})))'

def W(p, q):
    return f'(G ({p})) | ({p} U ({q}))'



def ouru(a, b):
    return f'(({a}) & X (({b}) R ({a})))'

def athenb(a, b):
    return f'(F({a}) & (X({b}) R ({a})))'

a = 'only_in_lane1'
b = 'only_in_junction'
c = 'only_in_lane2'
d = 'lane1_match_lane2'
# a = 'a'
# b = 'b'
# c = 'c'

# print(f'{W(a, W(b, c))} -> {W(a, W(b, f"{c} & {d}"))}')

# print(athenb(athenb(a, b), c))
p = 'a & (X(b) R a)'
q = 'c & d'
# print(W(p, q))

# print(ouru(ouru(a, b), c))
#
# data = f'(({a} & X({b}) & X(X((({b} & !({c}) & !({d})) U ({c} | {d}))))) -> ({a} & X({b}) & X(X((({b} & !({c}) & !({d})) U {d})))))'

print(f'(({a} & X({b}) & X(X((({b} & !({c})) U ({c} | !({b})))))) -> ({a} & X({b}) & X(X((({b} & !({c})) U ({c} & {d}))))))')