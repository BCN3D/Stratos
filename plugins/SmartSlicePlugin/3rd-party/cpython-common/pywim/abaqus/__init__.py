
class DataLine(object):
    def __init__(self, data=[]):
        self.data = data

    # Converts each data item to the corresponding type given in *args
    def cast(self, *args):
        items = []
        for i in range(len(self.data)):
            if len(args) <= i:
                dtype = args[-1]
            else:
                dtype = args[i]
            items.append(dtype(self.data[i]))
        return items

class Parameter(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Keyword(object):
    def __init__(self, name):
        self.name = name
        self.params = []
        self.datalines = []

    def has_param(self, name):
        return any([p.name == name for p in self.params])

    def param_value(self, name, default=None):
        p = self.param_by_name(name)
        if p:
            return p.value
        return default

    def param_by_name(self, name):
        for p in self.params:
            if p.name == name:
                return p
        return None

    def cast_all_data(self, dtype=str):
        casted_data = []
        for dl in self.datalines:
            casted_data.extend(dl.cast(dtype))
        return casted_data

    def __eq__(self, other):
        if self.name == other.name:
            if len(self.params) == len(other.params):
                for i in range(len(self.params)):
                    if self.params[i] != other.params[i]:
                        return False
                return True
        return False

    def __str__(self):
        s = '*' + self.name
        for p in self.params:
            if p.value:
                s += ', %s=%s' % (p.name, p.value)
            else:
                s += p.name
        for dl in self.datalines:
            s += '\n' + ', '.join(dl.data)
        return s

class Input(object):
    def __init__(self):
        self.keywords = []

    def keywords_by_name(self, name):
        return [k for k in self.keywords if k.name == name]

    # Returns the first keyword that matches name after the given keyword, parent
    def child_keyword(self, parent, name, stop_name=None):
        found_k = False
        for k in self.keywords:
            if not found_k:
                found_k = k == parent
            else:
                if k.name == name:
                    return k
                if k.name == parent.name:
                    return None
                if stop_name and k.name == stop_name:
                    return None
        return None

    # Returns whether inner is wrapped by *outer and *END outer or not (e.g. is *NSET inside *PART/*ENDPART)
    def inside(self, inner, outer_name):
        in_outer = False
        outer_kw = None
        for k in self.keywords:
            if not in_outer and k.name == outer_name:
                in_outer = True
                outer_kw = k

            if in_outer and k.name == ('END' + outer_name):
                in_outer = False
                outer_kw = None

            if id(k) == id(inner):
                return outer_kw
        return None

    @staticmethod
    def _lines_to_keyword(lines):
        # TODO keyword param lines split over mutliple lines

        split_lines = []
        for l in lines:
            split_lines.append(l.rstrip(',').split(','))

        mainline = split_lines[0]

        kname = mainline[0].lstrip('*')
        k = Keyword(kname)

        if len(mainline) > 1: # has parameters
            for pdef in mainline[1:]:
                if '=' in pdef:
                    pname, pval = pdef.split('=')
                else:
                    pname = pdef
                    pval = None
                k.params.append(Parameter(pname, pval))

        # data lines
        if len(split_lines) > 1:
            for dl in split_lines[1:]:
                k.datalines.append(DataLine(dl))

        return k

    @classmethod
    def Parse(cls, file_name):
        inp = cls()

        with open(file_name, 'r') as inpf:
            inplines = inpf.readlines()

        # Format all lines
        for i in range(len(inplines)):
            fmt_line = inplines[i].rstrip('\r\n')

            fmt_line = fmt_line.upper()
            fmt_line = fmt_line.replace(' ', '')

            inplines[i] = fmt_line

        # Find indices of all comments
        comment_indices = []
        for i in range(len(inplines)):
            if inplines[i].startswith('**'):
                comment_indices.append(i)

        # Remove all comments
        for i in sorted(comment_indices, reverse=True):
            del inplines[i]

        # Loop through and get lines for each keyword and process them into Keyword objects
        in_keyword = False
        keyword_lines = []
        for line in inplines:
            if line.startswith('*'):
                if len(keyword_lines) > 0:
                    new_keyword = Input._lines_to_keyword(keyword_lines)
                    inp.keywords.append(new_keyword)

                keyword_lines = [line]
            else:
                keyword_lines.append(line)

        # last keyword
        if len(keyword_lines) > 0:
            new_keyword = Input._lines_to_keyword(keyword_lines)
            inp.keywords.append(new_keyword)

        return inp

