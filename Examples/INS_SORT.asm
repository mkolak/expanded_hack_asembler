@10
D=A
@length
M=D

@100
D=A
@start
M=D

@i
M=1

(FOR)

    @i
    D=M
    @length
    D=M-D
    @ENDFOR
    D;JEQ

    @i
    D=M
    @start
    D=M+D
    A=D
    D=M
    @key
    M=D

    @i
    D=M
    @j
    M=D-1

    (FOR_1)
        
        @j
        D=M+1
        @ENDFOR_1
        D;JEQ

        @j
        D=M
        @start
        D=M+D
        A=D
        D=M
        @key
        D=D-M
        @ENDFOR_1
        D;JLE

        @j
        D=M
        @start
        D=M+D
        A=D
        D=M
        A=A+1
        M=D

        @j
        M=M-1

        @FOR_1
        0;JMP

    (ENDFOR_1)

    @j
    D=M+1
    @start
    D=M+D
    @swap_addr
    M=D
    @key
    D=M
    @swap_addr
    A=M
    M=D

    @i
    M=M+1    

    @FOR
    0;JMP

(ENDFOR)
(END)
@END
0;JMP