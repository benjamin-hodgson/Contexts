import sys
import contexts

def main():
	result = contexts.run('.')
	if not result:
		sys.exit(1)
	sys.exit(0)
