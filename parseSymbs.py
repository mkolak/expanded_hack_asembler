def _parse_symbs(self):
    # Prvo parsiramo deklaracije oznaka. Npr. "(LOOP)".
    self._iter_lines(self._parse_lab)

    # Na kraju parsiramo varijable i reference na oznake te ih pretvaramo u
    # konstante. Npr. "@SCREEN" pretvaramo u "@16384" ili "@END" kojemu je
    # oznaka "(END)" bila u trecoj liniji pretvaramo u "@3".
    self._n = 16
    self._iter_lines(self._parse_var)


# Svaka oznaka mora biti sadrzana unutar oblih zagrada. Npr. "(LOOP)". Svaka
# oznaka koju procitamo treba zapamtiti broj linije u kojoj se nalazi i biti
# izbrisana iz nje. Koristimo dictionary _labels.
def _parse_lab(self, line, m, n):
    if line[0] != "(":
        return line
    l = line[1:].split(")")
    if len(l) != 2 or len(l[0]) == 0:
        self._flag = False
        self._errm = "Invalid label"
    elif len(l[1]) != 0:
        self._flag = False
        self._errm = "Invalid label"
    else:
        self._labels[l[0]] = str(m)
    return ""


# Svaki poziv na varijablu ili oznaku je oblika "@NAZIV", gdje naziv nije broj.
# Prvo provjeriti oznake ("_labels"), a potom varijable ("_vars"). Varijablama
# dodjeljujemo memorijske adrese pocevsi od 16. Ova funkcija nikad ne vraca
# prazan string!
def _parse_var(self, line, m, n):
    if line[0] != "@" or (line[0] == "@" and line[1:].isdigit()):
        return line
    l = line[1:]
    if l in self._labels.keys():
        return "@" + self._labels[l]
    elif l in self._vars.keys():
        return "@" + self._vars[l]
    else:
        self._vars[l] = str(self._n)
        self._n += 1
        return "@" + str(self._n - 1)


# Inicijalizacija predefiniranih oznaka.
def _init_symbs(self):
    self._labels = {
        "SCREEN": "16384",
        "KBD": "24576",
        "SP": "0",
        "LCL": "1",
        "ARG": "2",
        "THIS": "3",
        "THAT": "4",
    }
    for i in range(0, 16):
        self._labels["R" + str(i)] = str(i)