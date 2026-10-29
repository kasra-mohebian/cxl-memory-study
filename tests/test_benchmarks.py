"""Portable correctness tests. No hardware performance conclusions."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'benchmarks/src'

class Benchmarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.build = Path(cls.temp.name)
        cls.compiler = os.environ.get('CXX', 'c++')
        for name in ['memory_benchmark', 'page_benchmark', 'page_copy_benchmark', 'tier_decision_simulation']:
            subprocess.run([cls.compiler, '-std=c++17', '-O2', str(SRC / (name+'.cpp')),
                            '-o', str(cls.build/name)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_program(self, name, *args):
        return subprocess.run([str(self.build/name), *args], capture_output=True, text=True, timeout=15)

    def test_small_portable_runs(self):
        for name in ['memory_benchmark', 'page_benchmark', 'page_copy_benchmark']:
            with self.subTest(name=name):
                result = self.run_program(name, '1')
                self.assertEqual(result.returncode, 0, result.stderr)
                if name == 'page_copy_benchmark':
                    self.assertIn('Full-copy verification: passed', result.stdout)

    def test_invalid_sizes_fail_before_allocation(self):
        for name in ['memory_benchmark', 'page_benchmark', 'page_copy_benchmark']:
            for value in ['0', '-1', '+1', 'abc', '1x', '', '17592186044416', '18446744073709551616']:
                with self.subTest(name=name, value=value):
                    result = self.run_program(name, value)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertNotIn('bandwidth:', result.stdout)

    def test_copy_verifier_catches_removed_copy(self):
        text = (SRC/'page_copy_benchmark.cpp').read_text(encoding='utf-8')
        # Break each path independently: the random destination reset must matter.
        for pass_index in (0, 1):
            parts = text.split('std::memcpy(', 2)
            broken = parts[0] + ('std::memcmp(' if pass_index == 0 else 'std::memcpy(') + parts[1]
            broken += ('std::memcmp(' if pass_index == 1 else 'std::memcpy(') + parts[2]
            source = self.build/'broken.cpp'
            source.write_text(broken, encoding='utf-8')
            subprocess.run([self.compiler, '-std=c++17', '-O2', '-I', str(SRC), str(source),
                            '-o', str(self.build/'broken')], check=True, capture_output=True)
            result = self.run_program('broken', '1')
            self.assertEqual(result.returncode, 3)
            self.assertIn('verification failed', result.stderr)
            self.assertNotIn('bandwidth:', result.stdout)

    def test_simulation_is_repeatable_on_this_toolchain(self):
        one = self.run_program('tier_decision_simulation')
        two = self.run_program('tier_decision_simulation')
        self.assertEqual(one.returncode, 0)
        self.assertEqual(one.stdout, two.stdout)

    def test_copy_pattern_rejects_page_misplacement(self):
        source = self.build / 'pattern-test.cpp'
        source.write_text('''#include "benchmark_common.hpp"
#include <vector>
int main() {
    const size_t page = 4096;
    std::vector<char> bytes(259 * page + 3);
    fill_pattern(bytes.data(), bytes.size());
    if (verify_copy(bytes.data(), bytes.data() + 257 * page, page)) return 1;
    std::vector<char> copied = bytes;
    if (!verify_copy(bytes.data(), copied.data(), bytes.size())) return 2;
    std::memcpy(copied.data(), bytes.data() + 257 * page, page);
    if (verify_copy(bytes.data(), copied.data(), bytes.size())) return 3;
    return 0;
}
''', encoding='utf-8')
        subprocess.run([self.compiler, '-std=c++17', '-I', str(SRC), str(source),
                        '-o', str(self.build / 'pattern-test')], check=True, capture_output=True)
        self.assertEqual(self.run_program('pattern-test').returncode, 0)

    def test_runner_without_git_collects_metadata_before_command_failure(self):
        # Isolated source copy and fake commands: never run real benchmarks.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / 'benchmarks/scripts'
            scripts.mkdir(parents=True)
            shutil.copy(ROOT / 'benchmarks/scripts/run_benchmarks.sh', scripts)
            build = root / 'benchmarks/build'
            build.mkdir()
            for name in ['memory_benchmark', 'page_benchmark', 'page_copy_benchmark',
                         'inter_tier_copy_benchmark']:
                exe = build / name
                exe.write_text('#!/bin/sh\nexit 99\n')
                exe.chmod(0o755)
            tools = root / 'tools'
            tools.mkdir()
            for name, body in {
                'git': 'exit 128',
                'numactl': 'if [ "$1" = "-H" ]; then exit 7; fi\necho stub-benchmark-command >&2\nexit 9',
            }.items():
                exe = tools / name
                exe.write_text('#!/bin/sh\n' + body + '\n')
                exe.chmod(0o755)
            output = root / 'run'
            env = {**os.environ, 'PATH': str(tools) + os.pathsep + os.environ['PATH'],
                   'CPU_NODE': '0', 'RAM_NODE': '0', 'HBM_NODE': '0', 'CXL_NODE': '0',
                   'RUN_DIR': str(output)}
            result = subprocess.run(['bash', str(scripts / 'run_benchmarks.sh')],
                                    env=env, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)  # real command errors still fail closed
            metadata = (output / 'environment.txt').read_text()
            self.assertIn('source: not a git checkout', metadata)
            self.assertIn('numactl topology unavailable', metadata)
            self.assertTrue(any('stub-benchmark-command' in p.read_text()
                                for p in (output / 'raw').glob('*.stderr')))

    @unittest.skipUnless(os.environ.get('CHECK_NUMA') == '1', 'Requires Linux libnuma')
    def test_numa_invalid_node_is_rejected(self):
        exe = self.build/'inter_tier_copy_benchmark'
        subprocess.run([self.compiler, '-std=c++17', str(SRC/'inter_tier_copy_benchmark.cpp'),
                        '-lnuma', '-o', str(exe)], check=True, capture_output=True)
        result = self.run_program(exe.name, '0', '2147483647', '1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('bandwidth:', result.stdout)

if __name__ == '__main__':
    unittest.main()
