"""Run once after installing: checks Python, the skills and their validation."""
import sys

from skills_kit import load_skills, validate

print("Python", sys.version.split()[0])
skills = load_skills()
print(len(skills), "skills:", ", ".join(skills))
print("problems:", validate(skills) or "none")
print("setup ok")
