#    EncryptH. A SHA-3 encryption method made with code from the KangarooTwelve team.
#    Copyright (C) 2023 cocoazawa
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# DO NOT USE ONLINE OR ON AN ONLINE PLATFORM. 

fileURL = "input.mp4"

print("[STARTING] encryptH...")

def ROL64(a, n):
    return ((a >> (64-(n%64))) + (a << (n%64))) % (1 << 64)

def KeccakP1600onLanes(lanes, nrRounds):
    R = 1
    for round in range(24):
        if (round + nrRounds >= 24):
            # θ
            C = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
            D = [C[(x+4)%5] ^ ROL64(C[(x+1)%5], 1) for x in range(5)]
            lanes = [[lanes[x][y]^D[x] for y in range(5)] for x in range(5)]
            # ρ and π
            (x, y) = (1, 0)
            current = lanes[x][y]
            for t in range(24):
                (x, y) = (y, (2*x+3*y)%5)
                (current, lanes[x][y]) = (lanes[x][y], ROL64(current, (t+1)*(t+2)//2))
            # χ
            for y in range(5):
                T = [lanes[x][y] for x in range(5)]
                for x in range(5):
                    lanes[x][y] = T[x] ^((~T[(x+1)%5]) & T[(x+2)%5])
            # ι
            for j in range(7):
                R = ((R << 1) ^ ((R >> 7)*0x71)) % 256
                if (R & 2):
                    lanes[0][0] = lanes[0][0] ^ (1 << ((1<<j)-1))
        else:
            for j in range(7):
                R = ((R << 1) ^ ((R >> 7)*0x71)) % 256
    return lanes

def load64(b):
    return sum((b[i] << (8*i)) for i in range(8))

def store64(a):
    return bytearray((a >> (8*i)) % 256 for i in range(8))

def KeccakP1600(state, nrRounds):
    lanes = [[load64(state[8*(x+5*y):8*(x+5*y)+8]) for y in range(5)] for x in range(5)]
    lanes = KeccakP1600onLanes(lanes, nrRounds)
    state = bytearray().join([store64(lanes[x][y]) for y in range(5) for x in range(5)])
    return bytearray(state)

def TurboSHAKE(c, M, D, outputByteLen):
    outputBytes = bytearray()
    state = bytearray([0 for i in range(200)])
    rateInBytes = (1600-c)//8
    blockSize = 0
    inputOffset = 0
    # === Absorb all the input blocks ===
    while(inputOffset < len(M)):
        blockSize = min(len(M)-inputOffset, rateInBytes)
        for i in range(blockSize):
            state[i] = state[i] ^ M[i+inputOffset]
        inputOffset = inputOffset + blockSize
        if (blockSize == rateInBytes):
            state = KeccakP1600(state, 12)
            blockSize = 0
    # === Do the padding and switch to the squeezing phase ===
    state[blockSize] = state[blockSize] ^ D
    if (((D & 0x80) != 0) and (blockSize == (rateInBytes-1))):
        state = KeccakP1600(state, 12)
    state[rateInBytes-1] = state[rateInBytes-1] ^ 0x80
    state = KeccakP1600(state, 12)
    # === Squeeze out all the output blocks ===
    while(outputByteLen > 0):
        blockSize = min(outputByteLen, rateInBytes)
        outputBytes = outputBytes + state[0:blockSize]
        outputByteLen = outputByteLen - blockSize
        if (outputByteLen > 0):
            state = KeccakP1600(state, 12)
    return outputBytes

def TurboSHAKE128(M, D, outputByteLen):
    return TurboSHAKE(256, M, D, outputByteLen)

def TurboSHAKE256(M, D, outputByteLen):
    return TurboSHAKE(512, M, D, outputByteLen)

def right_encode(x):
    S = bytearray()
    while(x > 0):
        S = bytearray([x % 256]) + S
        x = x//256
    S = S + bytearray([len(S)])
    return S

# inputMessage and customizationString must be of type byte string or byte array
def KangarooTwelve(inputMessage, customizationString, outputByteLen):
    B = 8192
    c = 256
    S = bytearray(inputMessage) + bytearray(customizationString) + right_encode(len(customizationString))
    # === Cut the input string into chunks of B bytes ===
    n = (len(S)+B-1)//B
    Si = [bytearray(S[i*B:(i+1)*B]) for i in range(n)]
    if (n == 1):
        # === Process the tree with only a final node ===
        return TurboSHAKE128(Si[0], 0x07, outputByteLen)
    else:
        # === Process the tree with kangaroo hopping ===
        CVi = [TurboSHAKE128(Si[i+1], 0x0B, c//8) for i in range(n-1)]
        NodeStar = Si[0] + bytearray([3,0,0,0,0,0,0,0]) + bytearray().join(CVi) \
            + right_encode(n-1) + b'\xFF\xFF'
        return TurboSHAKE128(NodeStar, 0x06, outputByteLen)

def outputHex(s):
    hashArray = []
    for i in range(len(s)):
        hexLocal = ("{0:02x}".format(s[i]))
        hashArray.append(f"{hexLocal}")
    return hashArray

print("[STARTING] Locating and reading file... ")

inputEizou = open(fileURL, "r+b")
contentsOfFile = inputEizou.read()
print(f"[ RESULT ] File type: {type(contentsOfFile)}")
print(f"[ RESULT ] File length: {len(contentsOfFile)}")
print(f"[  CALC  ] Approx time: {len(contentsOfFile) * 119 / 13783802} seconds")
print()
print(f"[STARTING] Content transfer into bytearray...")

contentsOfFile = contentsOfFile.decode('utf-8', 'backslashreplace')
byteArrayGlobalInput = bytes(rf"{contentsOfFile}", encoding="utf-8")
print(f"[ RESULT ] Content type: {type(byteArrayGlobalInput)}")
print(f"[ RESULT ] Official input cut to 100 characters: {byteArrayGlobalInput[0:100]}")

print()
print(f"[STARTING] KangarooTwelve and thus the encryption and hash generation of the file...")

output = outputHex(KangarooTwelve(byteArrayGlobalInput, b'nistThanks', 512))
emptySpacer = " "
noSpacer = ""

print(f"[  DONE  ] Output results:")
print(f"[ RESULT ] Output: {emptySpacer.join(output)}")
print(f"[ RESULT ] Output (non-spaced hash): {noSpacer.join(output)}")

print(f"[   OK   ] Done.")
