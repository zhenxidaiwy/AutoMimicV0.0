"""Add any new hand-written lessons of library.LESSONS to library.json (idempotent)."""
import library as libm

lib = libm.load()
n = len(lib["checks"])
libm.seed_lessons(lib)
libm.save(lib)
print(f"library checks {n} -> {len(lib['checks'])}")
