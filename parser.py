import sys


class Parser:
    def __init__(self, filename):
        # Otvaramo input asemblersku datoteku.
        try:
            self._file = open(filename + ".asm", "r")
        except:
            Parser._error("File", -1, "Cannot open source file.")
            return

        # Pogreske prilikom parsiranja.
        self._flag = True  # Ukoliko je flag postavljen na False, parsiranje je
        # neuspjesno.
        self._line = -1  # lokacija (broj linije) na kojoj se pogreska nalazi.
        self._errm = ""  # Poruka koja opisuje pogresku.

        # Linije iz input datoteke upisujuemo u ovu listu.
        self._lines = []

        # Inicijalizacija varijabli i simbola.
        self._labels = {}
        self._vars = {}
        self._init_symbs()

        # Inicijalizacija naredbi.
        self._init_comms()

        # Citamo input datoteku.
        try:
            self._read_file()
        except:
            Parser._error("File", -1, "Cannot read source file.")
            return

        # Parsiramo linije izvornog koda.
        self._parse_lines()
        if not self._flag:
            Parser._error("C&W", self._line, self._errm)

        self._parse_macros()
        if not self._flag:
            Parser._error("MAC", self._line, self._errm)

        self._parse_symbs()
        if not self._flag:
            Parser._error("LAB", self._line, self._errm)

        self._parse_comms()
        if not self._flag:
            Parser._error("COM", self._line, self._errm)

        # IDEJA
        # 1. Iz asemblerske datoteke izbaciti sve razmake i komentare. Sjetite
        #    se kako komentari u hack asembleru mogu biti jednolinijski i
        #    viselinijski.
        # 2. Sve simbole i varijable pretvoriti u numericke adrese (brojevi
        #    linija ili adrese u memoriji).
        # 3. Parsirati naredbe (A i C-instrukcije).

        # Na kraju parsiranja strojni kod upisujemo u ".hack" datoteku.
        try:
            self._file = open(filename + ".hack", "w")
        except:
            Parser._error("File", -1, "Cannot open destination file.")
            return

        try:
            self._write_file()
        except:
            Parser._error("File", -1, "Cannot write to destination file.")
            return

    from parseLines import _parse_lines, _parse_comments
    from parseSymbs import _parse_symbs, _init_symbs, _parse_lab, _parse_var
    from parseComms import _parse_comms, _init_comms, _parse_comm
    from parseMacros import _parse_macros, _parse_mac

    @staticmethod
    def _error(src, line, msg):
        if len(src) > 0 and line > -1:
            print("[" + src + ", " + str(line) + "]" + msg)
        elif len(src) > 0:
            print("[" + src + "] " + msg)
        else:
            print(msg)

    # Funkcija koja cita input datoteku te svaki redak sprema u listu uredjenih
    # trojki kojima su koordinate
    #   1. originalna linija iz datoteke
    #   2. broj linije u parsiranoj datoteci (u pocetku isti kao 3.)
    #   3. broj linije u originalnoj datoteci
    def _read_file(self):
        n = 0
        for line in self._file:
            self._lines.append((line, n, n))
            n += 1

    # Funkcija upisuje parsirane linije u output ".hack" datoteku.
    def _write_file(self):
        for (line, i, j) in self._lines:
            self._file.write(line)
            if i < len(self._lines) - 1:
                self._file.write("\n")

    # Funkcija iterira procitanim linijama i na svaku primjenjuje funkciju
    # "func". Funkcija "func" vraća string koji odgovara vrijednosti parsirane
    # linije.
    #
    # Primjer:
    # ("@END", 4, 4) postaje ("@3", 3, 4)
    #
    # Ukoliko je duljina vracene linije 0, tu liniju brisemo. Takodjer, svaka
    # funkcija "func" mora se brinuti o pogreskama na koje moze naici (npr.
    # viselinijski komentari koji nisu zatvoreni ili pogresna naredba M=B+1).
    def _iter_lines(self, func):
        lines = []
        i = 0
        for (line, m, n) in self._lines:
            l = func(line, i, n)
            if not self._flag:
                self._line = n
                break
            if type(l) is list:
                lines += l
                i += len(l)
            elif len(l) > 0:
                lines.append((l, i, n))
                i += 1
        self._lines = lines


def main():
    if len(sys.argv) < 2:
        print("[Error] Isufficient arguments. Specify file to parse.")
        exit(1)
    file = sys.argv[1].split(".asm")[0]
    Parser(file)


if __name__ == "__main__":
    main()
