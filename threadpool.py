#!/usr/bin/env python

"""
Copyright (c) 2011, Etienne Perot
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import threading

class threadpool(threading.Thread):
	class _poolworker(threading.Thread):
		def __init__(self, pool):
			self._pool = pool
			self._lock = threading.RLock()
			self._stateChange = threading.Condition(self._lock)
			self._task = None
			self._decommissioned = False
			threading.Thread.__init__(self)
			self.start()
		def runTask(self, task):
			with self._lock:
				if not self._decommissioned:
					self._task = task
					self._stateChange.notifyAll()
		def decommission(self):
			with self._lock:
				self._decommissioned = True
				self._stateChange.notifyAll()
		def run(self):
			with self._lock:
				while True:
					while self._task is None and not self._decommissioned:
						self._stateChange.wait()
					if self._task is not None:
						(self._task[0])(*(self._task[1]), **(self._task[2]))
						self._task = None
						self._pool._taskFinished(self)
					if self._decommissioned:
						break
	def __init__(self, numThreads=4, defaultTarget=None):
		self._numThreads = numThreads
		self._defaultTarget = defaultTarget
		self._tasks = []
		self._numSpawned = 0
		self._numBusy = 0
		self._availableThreads = []
		self._lock = threading.RLock()
		self._taskChange = threading.Condition(self._lock)
		self._shutdownCondition = threading.Condition(self._lock)
		self._shuttingDown = False
		threading.Thread.__init__(self)
		self.start()
	def add(self, target, *args, **kwargs):
		with self._lock:
			if not self._shuttingDown:
				self._tasks.append((target, args, kwargs))
				self._taskChange.notifyAll()
	def __call__(self, *args, **kwargs):
		if self._defaultTarget is not None:
			self.add(self._defaultTarget, *args, **kwargs)
		else:
			self.add(args[0], *(args[1:]), **kwargs)
	def _taskFinished(self, thread):
		with self._lock:
			self._availableThreads.append(thread)
			self._numBusy -= 1
			self._taskChange.notifyAll()
	def shutdown(self, blocking=True):
		with self._lock:
			self._shuttingDown = True
			self._taskChange.notifyAll()
			if blocking:
				self._shutdownCondition.wait()
	def _getWorkers(self, desired):
		freeWorkers = []
		with self._lock:
			prespawed = min(desired, len(self._availableThreads))
			freeWorkers.extend(self._availableThreads[:prespawed])
			self._availableThreads = self._availableThreads[prespawed:]
			if desired > len(freeWorkers) and self._numSpawned < self._numThreads:
				newWorkers = min(desired - len(freeWorkers), self._numThreads - self._numSpawned)
				for i in xrange(newWorkers):
					freeWorkers.append(threadpool._poolworker(self))
				self._numSpawned += newWorkers
		return freeWorkers
	def run(self):
		with self._lock:
			while True:
				self._taskChange.wait()
				if len(self._tasks):
					freeWorkers = self._getWorkers(len(self._tasks))
					for worker in freeWorkers:
						worker.runTask(self._tasks.pop(0))
					self._numBusy += len(freeWorkers)
				if self._shuttingDown and not len(self._tasks) and not self._numBusy:
					for thread in self._availableThreads:
						thread.decommission()
					self._shutdownCondition.notifyAll()
					break

if __name__ == '__main__':
	import sys, time, random
	printLock = threading.RLock()
	def p(*args):
		s = []
		for i in args:
			s.append(unicode(i))
		s = (u' '.join(s) + '\n').encode('utf8')
		with printLock:
			sys.stdout.write(s)
			sys.stdout.flush()
	def dummyTask(i, t):
		p('Task', i, 'started (sleeping', t, 'seconds).')
		time.sleep(t)
		p('Task', i, 'finished (sleeping', t, 'seconds).')
	pool = threadpool(numThreads=2, defaultTarget=dummyTask)
	for i in xrange(8):
		t = random.randint(3, 20)
		p('Task', i, 'adding (sleeping', t, 'seconds).')
		pool(i, t)
		p('Task', i, 'added (sleeping', t, 'seconds).')
		time.sleep(random.randint(0, 2))
	p('Done adding tasks.')
	pool.shutdown()
	p('Pool has shut down.')
