    state = ''
    max_state = -1
    max_symbol = -1
    i = []
    f = []
    s = []
    t = []
    with open(path, 'r') as mh:
        for line in mh:
            line = line.strip()
            if line[0] == 'I':
                state = 'I'
            elif line[0] == 'F':
                state = 'F'
            elif line[0] == 'S':
                state = 'S'
            elif line[0] == 'T':
                state = 'T'
            else:
                prob = float(line.split(' ')[1])
                symbols = map(int, (line.split(' ')[0]).translate(None, '()').split(','))
                if state == 'I':
                    if symbols[0] > max_state:
                        max_state = symbols[0]
                    i.append((symbols, prob))
                elif state == 'F':
                    if symbols[0] > max_state:
                        max_state = symbols[0]
                    f.append((symbols, prob))
                elif state == 'S':
                    if symbols[0] > max_state:
                        max_state = symbols[0]
                    if symbols[1] > max_symbol:
                        max_symbol = symbols[1]
                    s.append((symbols, prob))
                elif state == 'T':
                    max_t = max(symbols[0], symbols[2])
                    if max_t > max_state:
                        max_state = max_t
                    if symbols[1] > max_symbol:
                        max_symbol = symbols[1]
                    t.append((symbols, prob))
    #SECOND STEP: making the model
    ni = [.0 for _ in xrange(max_state + 1)]
    for sid, prob in i:
        ni[sid[0]] = prob
    nf = [.0 for _ in xrange(max_state + 1)]
    for sid, prob in f:
        nf[sid[0]] = prob
    ns = [[.0 for _ in xrange(max_symbol + 1)] for _ in xrange(max_state + 1)]
    for sid, prob in s:
        ns[sid[0]][sid[1]] = prob
    net = [[[.0 for _ in xrange(max_state + 1)] for _ in xrange(max_state + 1)] for _ in xrange(max_symbol + 1)]
    for sid, prob in t:
        net[sid[1]][sid[0]][sid[2]] = prob
    return np.array(ni), np.array(nf), np.array(ns), np.array(net)