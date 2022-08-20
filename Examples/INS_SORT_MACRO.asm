// INIT DATA
$LD(@100,33)
$LD(@101,3)
$LD(@102,113)
$LD(@103,313)
$LD(@104,334)
$LD(@105,35)
$LD(@106,22)
$LD(@107,215)
$LD(@108,1)
$LD(@109,53)
// INIT VARS
$LD(@start,100)
$LD(@length,10)
// INIT COUNTER
$LD(@i,1)
$SUB(D,@length,@i)
$LOOP(D){
    $ADD(A,@start,@i)
    $LD(@key,M)
    $SUB(@j,@i,1)
    $ADD(D,@j,1)
    $LOOP(D){
        $ADD(A,@start,@j)
        $SUB(D,@key,M)
        @LOOP1_END
        D;JGE
        $ADD(A,@start,@j)
        $LD(@help,M)
        $ADD(D,@j,1)
        $ADD(A,@start,D)
        $LD(M,@help)
        $SUB(@j,@j,1)
        $ADD(D,@j,1)
    }
    $ADD(D,@j,1)
    $ADD(A,@start,D)
    $LD(M,@key)
        
    // INCREMENT AND CHECK
    $ADD(@i,@i,1)
    $SUB(D,@length,@i)
}
(END)
@END
0;JMP