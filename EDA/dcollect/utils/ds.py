class merge:
    @staticmethod
    def dictlist(dicts: list) -> dict:
        ret = None
        for d in dicts:
            if d:
                if not ret:
                    ret = dict()
                ret.update(d)
        return ret

    @staticmethod
    def dicts(*args) -> dict:
        return merge.dictlist(list(args))

    @staticmethod
    def translate(templ: dict, trans: dict) -> dict:
        if not (isinstance(templ, dict) and \
                isinstance(trans, dict)):
            return

        for (k_templ, k_trans) in zip(templ, trans):
            o_trans = trans[k_trans]
            if isinstance(o_trans, dict):
                merge.translate(templ[k_templ], o_trans)
            elif callable(o_trans):
                templ[k_templ] = o_trans() if o_trans else None

        return templ

class select:
    @staticmethod
    def fromdict(o: dict, renamed_keys: dict, encoder = None):
        if o == None:
            return None

        ret = {}
        for old_k, new_k in renamed_keys.items():
            v = o.get(old_k)
            if v == None:
                continue
            if isinstance(new_k, dict):
                ret[old_k] = select.fromdict(v, new_k, encoder)
            else:
                ret[new_k or old_k] = v if not encoder else encoder(v)

        return ret

    @staticmethod
    def descend(o: dict, keys: list):
        curr_v = o
        for k in keys:
            if not isinstance(curr_v, dict):
                return curr_v
            curr_v = curr_v.get(k)
            if curr_v == None:
                break
        return curr_v
