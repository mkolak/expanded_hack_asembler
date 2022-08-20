def _parse_macros(self):

    # Varijabla koja sluzi kao flag u trenutku kada smo pozvali naredbu IF ili LOOP i ocekujemo da prvi iduci znak bude "{". Ponistava se cim se ostvari trazeno
    self._expect_open_bracket = False

    # Stog koji koristimo za unaprijed zapisivanje asemblerskog koda koji sluzi za zatvaranje nekog bloka otvorenog naredbama IF ili LOOP
    self._brackets_to_close = []
    # Pomocna varijabla za razlikovanje labela
    self._block_counter = 0

    self._iter_lines(self._parse_mac)

    # U slucaju da imamo nezatvorenih blokova koda na kraju datoteke, imamo pogresku
    if self._brackets_to_close and self._flag:
        self._flag = False
        self._errm = "Failed to close all code blocks"


# parse_mac funkcija proslijedenu liniju koda prepoznaje i obrađuje ukoliko je ona makro naredba.
# U prvih nekoliko linija vrsi se validacija. Ispitujemo da li je imamo otvorenu/zatvorenu zagradu, postoji li sadrzaj poslije zatvorene zagrade
# Poslije osnovnih provjera, provjeravamo je li naziv makro naredbe koju pozivamo ispravno i pozivamo daljnju funkciju za odgovarajucu naredbu
# u kojoj ce se makro naredba pretvoriti u asemblerski kod.


def _parse_mac(self, line, m, n):
    if self._expect_open_bracket and line != "{":
        self._flag = False
        self._errm = "Code block not opened properly"
        return []
    elif not self._expect_open_bracket and line == "{":
        self._flag = False
        self._errm = "Improperly opened block"
        return []
    elif line == "{":
        self._expect_open_bracket = False
        return []
    elif line == "}":
        return _parse_close(self, m, n)
    if line[0] != "$":
        return line
    macro_lines = []
    validate_closed = line[1:].split(")")
    if len(validate_closed) != 2:
        self._flag = False
        self._errm = "Improperly closed bracket"
        return macro_lines
    elif len(validate_closed[1]) > 0:
        self._flag = False
        self._errm = "Improper macro statement"
        return macro_lines
    validate_open = validate_closed[0].split("(")
    if len(validate_open) != 2:
        self._flag = False
        self._errm = "Improperly opened bracket"
        return macro_lines
    command = validate_open[0]
    args = validate_open[1].split(",")
    if command == "LD":
        macro_lines = _parse_LD(self, args, m, n)
    elif command == "ADD":
        macro_lines = _parse_ADD(self, args, m, n)
    elif command == "SUB":
        macro_lines = _parse_SUB(self, args, m, n)
    elif command == "SWAP":
        macro_lines = _parse_SWAP(self, args, m, n)
    elif command == "AND":
        macro_lines = _parse_AND_OR(self, args, m, n, "&")
    elif command == "OR":
        macro_lines = _parse_AND_OR(self, args, m, n, "|")
    elif command == "XOR":
        macro_lines = _parse_XOR(self, args, m, n)
    elif command == "NOT":
        macro_lines = _parse_NOT(self, args, m, n)
    elif command == "IF":
        macro_lines = _parse_IF(self, args, m, n)
    elif command == "LOOP":
        macro_lines = _parse_LOOP(self, args, m, n)
    else:
        self._flag = False
        self._errm = "Invalid macro command"
        return macro_lines
    return macro_lines


# U svakoj makro naredbi veliku ulogu imati ce vrsta memorijske lokacije u koju spremamo sadrzaj i vrsta operanada
# nad kojima cemo vrsiti makro operacije. Kako bi asemblerski kod bio optimiziran(ili uopce izvediv) za neke operacije,
# potrebno je odrediti klasifikaciju argumenata pomocu funkcija _classify_dst() i _classify_src()


def _classify_dst(dst):
    if dst in ["A", "M", "D", "AM", "AD", "AMD", "MD"]:
        return "REGISTER"
    elif dst[0] == "@":
        return "MEM_LOC"
    else:
        return "INVALID"


def _classify_src(src):
    if src in ["A", "M", "D"]:
        return "REGISTER"
    elif src[0] == "@":
        return "MEM_LOC"
    elif src.isdigit():
        return "CONSTANT"
    else:
        return "INVALID"


# Helper funkcija za skracivanje koda u formatiranim stringovima.


def a_or_m(state):
    return "M" if state == "MEM_LOC" else "A" if state == "CONSTANT" else "NEITHER"


# $LD(DST,SRC) makro naredba
# Prvo vrsimo provjeru broja argumenata i vracamo gresku u slucaju ako taj broj nije 2. Zatim klasificiramo argumente
# Ukoliko imamo argument koji nije validan, vracamo gresku
# Zatim krecemo u pretvorbu u asemblerski kod, koji se razlikuje u nekoliko slucajeva:
# 1. Argumenti su jednaki => vracamo praznu liniju jer kod ne mora nista raditi
# 2. DST je memorijska lokacija. String moze varirati u ovisnosti o SRC
# 3. DST je registar, a SRC je memorijska lokacija ili konstanta
# 4. DST i SRC su registri.


def _parse_LD(self, args, m, n):
    if len(args) != 2:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src = args
    args_class = [_classify_dst(dst), _classify_src(src)]
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if dst == src:
        return []
    if args_class[1] == "CONSTANT":
        src = "@" + src
    content = ""
    if args_class[0] == "MEM_LOC":
        content = f'{src + " " if args_class[1] != "REGISTER" else ""}D={src if args_class[1] == "REGISTER" else a_or_m(args_class[1])} {dst} M=D'
    elif args_class[0] == "REGISTER" and args_class[1] in ["MEM_LOC", "CONSTANT"]:
        content = f'{"D=A @tmp M=D " if "M" in dst else ""}{src} {"D="+a_or_m(args_class[1])+" @tmp A=M " if "M" in dst else ""}{dst + "=D"}'
    elif args_class == ["REGISTER", "REGISTER"]:
        content = dst + "=" + src
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $ADD(DST,SRC1,SRC2) makro naredba
# Kao i prethodna naredba, prvo vrsimo provjeru broja argumenata, zatim klasifikaciju, te validiramo argumente.
# Izmedu se dogadaju zamjene mjesta koje ce nam olaksati kasniju pretvorbu naredbe u asemblerski kod.
# Prilikom pretvorbe u asemblerski kod imamo nekoliko slucajeva:
# 1. Sva tri argumenta su jednaka
# 2. Dva operanda su jednaka. Ovdje se prvi put susrecemo sa posebnim slucajem pohranjujemo u registar M. Tada uvijek moramo pisati dodatan kod
#    kako bi osigurali da je upamcena adresa uz koju je vezan registar M, u trenutku prije poziva makro naredbe. Ovaj problem ce se pojavljivati i naknadno.
# 3. Jedan od operanada je jednak lokaciji za pohranu rezultata
# 4. Sva tri argumenta su razlicita.
#    Ovdje imamo 3 podslucaja: Prvi je kada su sva tri argumenta registri. Drugi je posebni slucaj kada pohranjujemo u M registar(moramo pamtiti adresu)
#    i kada imamo kombinaciju argumenata gdje je jedan memorijska lokacija, a drugi registar. Poslijednji, najucestaliji slucajevi su svi ostali koji se mogu
#    razrijesiti pomocu jednog templatea.


def _parse_ADD(self, args, m, n):
    if len(args) != 3:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src1, src2 = args
    args_class = [_classify_dst(dst), _classify_src(src1), _classify_src(src2)]
    if args_class[2] == "REGISTER" and src1 != "D":
        args_class[1], args_class[2] = args_class[2], args_class[1]
        src1, src2 = src2, src1
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    content = ""
    if dst == src1 == src2:
        content = (
            f'{dst + " " if args_class[0] == "MEM_LOC" else ""}{"A=" if dst == "D" else "D="}'
            f'{"M M=D+M" if args_class[0] == "MEM_LOC" else dst + " " + dst + "=D+" + ("A" if dst == "D" else dst)}'
        )
    elif src1 == src2:
        if args_class[1] == "CONSTANT":
            src1 = "@" + src1
        if args_class[2] == "CONSTANT":
            src2 = "@" + src2
        content = (
            f'{"D=A @tmp M=D " if "M" in dst and args_class[1] != "REGISTER" else ""}'
            f'{src1 + " " if args_class[1] != "REGISTER" else ""}'
            f'{"A=" if "D" == src1 else "D="}{src1 if args_class[1] == "REGISTER" else a_or_m(args_class[1])} '
            f'D=D+{"A" if "D" == src1 else src1 if args_class[1] == "REGISTER" else a_or_m(args_class[1])} '
            f'{dst + " M=D" if args_class[0] != "REGISTER" else "@tmp A=M M=D" if "M" in dst and args_class[1] != "REGISTER" else dst + "=D"}'
        )
    elif dst == src1 or dst == src2:
        if dst == src2:
            args_class[1], args_class[2] = args_class[2], args_class[1]
            src1, src2 = src2, src1
        if args_class[2] == "CONSTANT":
            src2 = "@" + src2
        if args_class[0] == "MEM_LOC":
            content = f'{src2 + " " if args_class[2] != "REGISTER" else ""}D={src2 if args_class[2] == "REGISTER" else a_or_m(args_class[2])} {dst} M=D+M'
        else:
            if args_class[2] == "REGISTER":
                content = f'{"D=" + src2 + " " if dst != "D" else ""}{dst}=D+{dst if dst != "D" else src2}'
            else:
                content = (
                    f'{"D=A @tmp M=D A=M D=M " if "M" == dst else "D=A " if "A" == dst else ""}'
                    f'{src2} D=D+M{" @tmp A=M M=D" if "M" == dst else " A=D" if "A" == dst else ""}'
                )
    else:
        if args_class[1] == "CONSTANT":
            src1 = "@" + src1
        if args_class[2] == "CONSTANT":
            src2 = "@" + src2
        if args_class == ["REGISTER", "REGISTER", "REGISTER"]:
            content = (
                f'{"D=" + src1 + " " if "D" == dst else ""}'
                f'{"D=D+"+src2}'
                f'{" " + dst + "=D" if dst != "D" else ""}'
            )
        elif (
            "M" in dst
            and args_class[1] == "REGISTER"
            and args_class[2] in ["MEM_LOC", "CONSTANT"]
        ):
            content = (
                f'{"M=D " if "D" == src1 else ""}'
                f"D=A @tmp M=D {src2} D={a_or_m(args_class[2])} @tmp "
                f'{"A=M M=D+M" if src1 == "D" else "D=D+M A=M M=D"}'
            )
        else:
            content = (
                f'{"D=A @tmp M=D " if "M" in dst else ""}'
                f'{src1 + " " if args_class[1] != "REGISTER" else ""}'
                f'{"D=" + src1 + " " if args_class[1] == "REGISTER" and src1 != "D" else "D=" + a_or_m(args_class[1]) + " " if src1 != "D" else ""}'
                f'{src2 + " " if args_class[2] != "REGISTER" else ""}'
                f'{dst if args_class[0] == "REGISTER" and "M" not in dst else "D"}=D+{src2 if args_class[2] == "REGISTER" else a_or_m(args_class[2])}'
                f'{" @tmp A=M M=D" if "M" in dst else ""}'
                f'{" " + dst + " M=D" if args_class[0] != "REGISTER" else ""}'
            )
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $SUB(DST,SRC1,SRC2)
# U pocetku vrsimo provjeru broja argumenata, klasificiramo argumente i provjeravamo jesu li validni.
# U nastavku vrsimo pretvorbu u asemblerski kod koja je u ovom slucaju jednostavnija jer se naredba SUB moze svesti na naredbe LD i ADD ovisno o slucaju
# 1. U slucaju da su src1 i src2 jednaki, rezultat operacije SUB je sigurno 0, pa pozivamo $LD(DST,0)
# 2. U suprotnom, sve ostale slucajeve mozemo svesti na operaciju zbrajanja, pri cemu imamo podslucajeve samo ovisno o tome kojem cemo argumentu promjeniti predznak.


def _parse_SUB(self, args, m, n):
    if len(args) != 3:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src1, src2 = args
    args_class = [_classify_dst(dst), _classify_src(src1), _classify_src(src2)]
    swapped = False
    if args_class[2] == "REGISTER" and src1 != "D":
        args_class[1], args_class[2] = args_class[2], args_class[1]
        src1, src2 = src2, src1
        swapped = True
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if src1 == src2:
        return _parse_LD(self, [dst, "0"], m, n)
    else:
        if args_class[1] == "REGISTER":
            prepend = f"D=-{src1}"
            append = f'{dst+"=-"+dst if args_class[0] == "REGISTER" else "M=-M"}'
            mid = _parse_ADD(self, [dst, "D", src2], m + 1, n)
            return (
                [(prepend, m, n)]
                + mid
                + ([(append, m + 1 + len(mid), n)] if not swapped else [])
            )
        elif "M" not in dst:
            return [
                (f"{'@' if args_class[2] == 'CONSTANT' else ''}{src2}", m, n),
                (f"D=-{a_or_m(args_class[2])}", m + 1, n),
            ] + _parse_ADD(self, [dst, src1, "D"], m + 2, n)
        else:
            content = f"D=A @tmp M=D {'@' if args_class[2] == 'CONSTANT' else ''}{src2} D=-{a_or_m(args_class[2])} {src1} D=D+{a_or_m(args_class[1])} @tmp A=M M=D"
            return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $AND(DST,SRC1,SRC2) i $OR(DST,SRC1,SRC2)
# Ove dvije makro naredbe parsiramo pomocu jedne funkcije jer se njihov asemblerski kod razlikuje samo po znaku za operaciju.
# Stovise, vecina koda i slucajeva je nalik na operaciju ADD, samo uz promjenu znaka za operaciju.
# Ipak ovdje imamo nesto manje slucajeva
# 1. Kada su src1 == src2, operaciju svodimo na $LD(dst, src1) u oba slucaja, jer src1 &| src1 ce sigurno biti src1
# 2. dst == src1 ili dst == src2
# 3. Sva tri argumenta su razlicita. Podslucajevi su ekvivalentni onima iz operacije ADD, mijenja se samo znak za operaciju


def _parse_AND_OR(self, args, m, n, oper):
    if len(args) != 3:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src1, src2 = args
    args_class = [_classify_dst(dst), _classify_src(src1), _classify_src(src2)]
    if args_class[2] == "REGISTER" and src1 != "D":
        args_class[1], args_class[2] = args_class[2], args_class[1]
        src1, src2 = src2, src1
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if src1 == src2:
        return _parse_LD(self, [dst, src1], m, n)
    content = ""
    if dst == src1 or dst == src2:
        if dst == src2:
            args_class[1], args_class[2] = args_class[2], args_class[1]
            src1, src2 = src2, src1
        if args_class[2] == "CONSTANT":
            src2 = "@" + src2
        if args_class[0] == "MEM_LOC":
            content = f'{src2 + " " if args_class[2] != "REGISTER" else ""}D={src2 if args_class[2] == "REGISTER" else a_or_m(args_class[2])} {dst} M=D{oper}M'
        else:
            if args_class[2] == "REGISTER":
                content = f'{"D=" + src2 + " " if dst != "D" else ""}{dst}=D{oper}{dst if dst != "D" else src2}'
            else:
                content = (
                    f'{"D=A @tmp M=D A=M D=M " if "M" == dst else "D=A " if "A" == dst else ""}'
                    f'{src2} D=D{oper}M{" @tmp A=M M=D" if "M" == dst else " A=D" if "A" == dst else ""}'
                )
    else:
        if args_class[1] == "CONSTANT":
            src1 = "@" + src1
        if args_class[2] == "CONSTANT":
            src2 = "@" + src2
        if args_class == ["REGISTER", "REGISTER", "REGISTER"]:
            content = (
                f'{"D=" + src1 + " " if "D" == dst else ""}'
                f'{"D=D" + oper + src2}'
                f'{" " + dst + "=D" if dst != "D" else ""}'
            )
        elif (
            "M" in dst
            and args_class[1] == "REGISTER"
            and args_class[2] in ["MEM_LOC", "CONSTANT"]
        ):
            content = (
                f'{"M=D " if "D" == src1 else ""}'
                f"D=A @tmp M=D {src2} D={a_or_m(args_class[2])} @tmp "
                f'{"A=M M=D" + oper + "M" if src1 == "D" else "D=D" + oper + "M A=M M=D"}'
            )
        else:
            content = (
                f'{"D=A @tmp M=D " if "M" in dst else ""}'
                f'{src1 + " " if args_class[1] != "REGISTER" else ""}'
                f'D={src1 if args_class[1] == "REGISTER" else a_or_m(args_class[1])} '
                f'{src2 + " " if args_class[2] != "REGISTER" else ""}'
                f'{dst if args_class[0] == "REGISTER" and "M" not in dst else "D"}=D{oper}{src2 if args_class[2] == "REGISTER" else a_or_m(args_class[2])}'
                f'{" @tmp A=M M=D" if "M" in dst else ""}'
                f'{" " + dst + " M=D" if args_class[0] != "REGISTER" else ""}'
            )
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $XOR(DST,SRC1,SRC2)
# Kao i ranije, zapocinjemo s provjerom broja argumenata i validacijom argumenta.
# Zatim pretvaramo u asemblerski kod prema slucajevima:
# 1. Ako su src1 == src2, tada samo pozivamo $LD(dst,0)
# 2. Ako pohranjujemo u "M" registar(pamtimo adresu M registra) i barem jedan od operanda je memorijska lokacija/konstanta
# 3. Ako su operandi oba registri
# 4. Svi ostali slucajevi


def _parse_XOR(self, args, m, n):
    if len(args) != 3:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src1, src2 = args
    args_class = [_classify_dst(dst), _classify_src(src1), _classify_src(src2)]
    if args_class[2] == "REGISTER" and src1 != "D":
        args_class[1], args_class[2] = args_class[2], args_class[1]
        src1, src2 = src2, src1
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if src1 == src2:
        return _parse_LD(self, [dst, "0"], m, n)
    if args_class[1] == "CONSTANT":
        src1 = "@" + src1
    if args_class[2] == "CONSTANT":
        src2 = "@" + src2
    if "M" in dst and src1 == "D" and src2 == "M":
        self._flag = False
        self._errm = "Operation is not possible"
        return []
    content = ""
    # TEMPLATE:
    # M=D if (src1 == D)
    # D=A
    # @tmpA
    # M=D
    # A=M if (src1 je REGISTAR)
    # D=M if (src1 je REGISTAR)
    # @MEM_LOC/CONST or @tmpB
    # M=D if (src1 je REGISTAR)
    # D=!M or D=!A (A if src1 je CONST)
    # @MEM_LOC/CONST2
    # D=D&M or D=D&A (A if src2 je CONST)
    # @tmp
    # M=D
    # @MEM_LOC/CONST2
    # D=!M or D=!A (A if src2 je CONST)
    # @MEM_LOC/CONST or @tmpB
    # D=D&M or D=D&A (A if src2 je CONST)
    # @tmp
    # D=D|M
    # @tmpA
    # A=M
    # M=D
    if "M" in dst and args_class[2] in ["MEM_LOC", "CONSTANT"] and src1 != "A":
        content = (
            f'{"M=D " if src1 == "D" else ""}'
            f'D=A @tmpA M=D {"A=M D=M @tmpB M=D" if args_class[1] == "REGISTER" else src1} D=!{"A" if args_class[1] == "CONSTANT" else "M"} '
            f'{src2} D=D&{a_or_m(args_class[2])} @tmp M=D {src2} D=!{a_or_m(args_class[2])} {"@tmpB" if args_class[1] == "REGISTER" else src1} '
            f'D=D&{"A" if args_class[1] == "CONSTANT" else "M"} @tmp D=D|M @tmpA A=M M=D'
        )
    elif args_class[1:] == ["REGISTER", "REGISTER"]:
        content = (
            f'{"A=M " if [src1, src2] == ["D","M"] else ""}{"M=D " if src1 == "D" else ""}D=A @tmpA M=D A=M D=M '
            f'@tmpB M=D D=!M @tmpA D=D&M @tmp M=D @tmpA D=!M @tmpB D=D&M @tmp {dst if args_class[0] == "REGISTER" and "M" not in dst else "D"}=D|M'
            f'{" @tmpA A=M M=D" if "M" in dst else " " + dst + " M=D" if args_class[0] != "REGISTER" else ""}'
        )
    else:
        content = (
            f'{"D=" + src1 + " " if src1 in "AM" else ""}{"@tmpA M=D" if args_class[1] == "REGISTER" else src1} '
            f'D=!{"M" if args_class[1] == "REGISTER" else a_or_m(args_class[1])} '
            f'{src2} D=D&{a_or_m(args_class[2])} @tmp M=D {src2} D=!{a_or_m(args_class[2])} {"@tmpA" if args_class[1] == "REGISTER" else src1} '
            f'D=D&{"M" if args_class[1] == "REGISTER" else a_or_m(args_class[1])} '
            f'@tmp {dst if args_class[0] == "REGISTER" else "D"}=D|M{" " + dst + " M=D" if args_class[0] != "REGISTER" else ""}'
        )
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $NOT(DST, SRC)
# Zapocnemo se provjerom broja argumenata i validacijom argumenata
# Imamo 3 slucaja:
# 1. Argumenti su jednaki
# 2. Specijalan slucaj kada je M registar odrediste, a memorijska lokacija ili konstanta operand
# 3. Svi ostali slucajevi spadaju u jedinstven template


def _parse_NOT(self, args, m, n):
    if len(args) != 2:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    dst, src = args
    args_class = [_classify_dst(dst), _classify_src(src)]
    if "INVALID" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    content = ""
    if dst == src:
        content = f'{dst + " " if args_class[0] != "REGISTER" else ""}{"M=!M" if args_class[0] != "REGISTER" else dst + "=!" + dst}'
    elif "M" in dst and args_class[1] != "REGISTER":
        if args_class[1] == "CONSTANT":
            src = "@" + src
        content = f"D=A @tmp M=D {src} D=!{a_or_m(args_class[1])} @tmp A=M M=D"
    else:
        if args_class[1] == "CONSTANT":
            src = "@" + src
        content = (
            f'{src + " " if args_class[1] != "REGISTER" else ""}'
            f'{dst if args_class[0] == "REGISTER" else "D"}=!{src if args_class[1] == "REGISTER" else a_or_m(args_class[1])}'
            f'{" " + dst + " M=D" if args_class[0] != "REGISTER" else ""}'
        )
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $SWAP(DST,DST)
# Swap zapocinjemo se provjerom broja argumenata i validacijom. U ovom slucaju validiramo pomocu classify_src
# jer ne zelimo da se medu argumentima pojave AD, AM, DM, AMD, a istovremeno odbacujemo i konstante i nevalidne argumente
# Slucajevi koje imamo:
# 1. isti argumenti, nema zamjene
# 2. Specijalni slucajevi D,A , A,M i D,M(nemoguc slucaj)
# 3. Slucajevi kada su argumenti razlicite vrste
# 4. Slucajevi kada su argumenti memorijske lokacije


def _parse_SWAP(self, args, m, n):
    if len(args) != 2:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    src1, src2 = args
    args_class = [_classify_src(src1), _classify_src(src2)]
    if args_class[1] == "REGISTER" and src1 != "D":
        args_class[0], args_class[1] = args_class[1], args_class[0]
        src1, src2 = src2, src1
    if "INVALID" in args_class or "CONSTANT" in args_class:
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if src1 == src2:
        return []
    if [src1, src2] == ["D", "M"]:
        self._flag = False
        self._errm = "Operation is not possible"
        return []
    content = ""
    if [src1, src2] == ["D", "A"]:
        content = "M=D D=A A=M"
    elif [src1, src2] == ["M", "A"] or [src1, src2] == ["A", "M"]:
        content = "D=M M=A A=D"
    elif args_class == ["REGISTER", "MEM_LOC"]:
        content = (
            f'{"D=A " if src1 in "AM" else ""}@tmp M=D {src2} D=M @tmpA M=D @tmp {"A=M " if "M" == src1 else ""}D=M {src2} M=D '
            f'@tmpA {src1 if "M" != src1 else "D"}=M{" @tmp A=M M=D" if src1 == "M" else ""}'
        )
    else:
        content = f"{src1} D=M @tmp M=D {src2} D=M {src1} M=D @tmp D=M {src2} M=D"
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# $IF(COND)
# Prvo vrsimo validaciju i klasifikaciju.
# Zatim zapisujemo pocetni dio IF-a
#
# @MEM_LOC/CONSTANT (?)
# D=M/A (?)
# @IF{NUMBER}_END
# D;JNE
#
# Taj komad koda funkcija parse_if vraca, dok se krajnji dio IF naredbe stavlja na stog "brackets_to_close" i zapisuje se onog trenutka kada
# naidemo na znak }. To ce znaciti da je to kraj bloka koji IF obuhvaca.
#
# Krajnji dio cini samo label: (IF{NUMBER}_END)
# Takoder, postavljamo "expect_open_bracket" na True, jer ocekujemo da je odmah slijedeci znak poslije IF naredbe znak "{".
# "block_counter" sluzi da mozemo ugraditi jedinstveni broj u label, tako da nema zabune na koji mjesto u kodu trebamo skociti


def _parse_IF(self, args, m, n):
    if len(args) != 1:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    cond = args[0]
    args_class = _classify_src(cond)
    if args_class == "INVALID":
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if args_class == "CONSTANT":
        cond = "@" + cond
    content = (
        f'{cond + " D=" + a_or_m(args_class) + " " if args_class != "REGISTER" else "D=" + cond + " " if cond in "AM" else ""}'
        f"@IF{self._block_counter}_END D;JNE"
    )
    self._expect_open_bracket = True
    self._brackets_to_close.append(f"(IF{self._block_counter}_END)")
    self._block_counter += 1
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]


# parse_close je pomocna funkcija koja sluzi da u trenutku kada naidemo na znak "}" za zatvaranje bloka, zapravo zatvorimo poslijednji otvoreni blok koda koji
# je otvoren prije znaka "}". To radimo tako da sa stoga "brackets_to_close" povucemo vec pripremljeni kod za zatvaranje poslijednjeg otvorenog bloka
# i zalijepimo ga na mjesto gdje smo pronasli "}" u datoteci. Naravno, ako nemamo nijedan otvoren blok koda a dosli smo do "}", imamo error.


def _parse_close(self, m, n):
    if self._brackets_to_close:
        l = self._brackets_to_close.pop()
        return [(l, m + i, n) for (i, l) in enumerate(l.split(" "))]
    else:
        self._flag = False
        self._errm = "Closing bracket with no open blocks"
        return []


# $LOOP(COND)
# Parsiranje loopa vrsi se na skoro identican nacin kao i if, samo sto im se razlikuje kod za otvaranje i zatvaranje bloka.


def _parse_LOOP(self, args, m, n):
    if len(args) != 1:
        self._flag = False
        self._errm = "Invalid number of arguments"
        return []
    cond = args[0]
    args_class = _classify_src(cond)
    if args_class == "INVALID":
        self._flag = False
        self._errm = "Invalid arguments"
        return []
    if args_class == "CONSTANT":
        cond = "@" + cond
    content = (
        f'{cond + " D=" + a_or_m(args_class) + " " if args_class != "REGISTER" else "D=" + cond + " " if cond in "AM" else ""}'
        f"@LOOP{self._block_counter}_END D;JEQ (LOOP{self._block_counter}_START)"
    )
    self._expect_open_bracket = True
    close_content = (
        f'{cond + " D=" + a_or_m(args_class) + " " if args_class != "REGISTER" else "D=" + cond + " " if cond in "AM" else ""}'
        f"@LOOP{self._block_counter}_START D;JNE (LOOP{self._block_counter}_END)"
    )
    self._brackets_to_close.append(close_content)
    self._block_counter += 1
    return [(l, m + i, n) for (i, l) in enumerate(content.split(" "))]
