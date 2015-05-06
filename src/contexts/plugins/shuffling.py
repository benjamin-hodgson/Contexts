import random


class Shuffler(object):
    def setup_parser(self, parser):
        parser.add_argument('--no-random',
                            action='store_false',
                            dest='shuffle',
                            default=True,
                            help="Disable test order randomisation.")

    def initialise(self, args, env):
        return args.shuffle

    def process_module_list(self, l):
        self.shuffle_list(l)

    def process_class_list(self, module, l):
        self.shuffle_list(l)

    def process_assertion_list(self, cls, l):
        self.shuffle_list(l)

    def shuffle_list(self, l):
        random.shuffle(l)

    def __eq__(self, other):
        return isinstance(other, Shuffler)
