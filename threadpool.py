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

import multiprocessing, threading

def _getResult(task, result, exception):
	return {
		'id': task[0],
		'target': task[1],
		'args': task[2],
		'kwargs': task[3],
		'result': result,
		'exception': exception
	}

class _threadpool(threading.Thread):
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
						result = None
						exception = None
						task = self._task
						try:
							result = (task[1])(*(task[2]), **(task[3]))
						except Exception, e:
							exception = e
						self._task = None
						self._pool._taskFinished(self, task, result, exception)
					if self._decommissioned:
						break
	def __init__(self, numThreads=4, defaultTarget=None):
		self._numThreads = numThreads
		self._defaultTarget = defaultTarget
		self._tasks = []
		self._results = []
		self._taskId = -1
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
				self._taskId += 1
				self._tasks.append((self._taskId, target, args, kwargs))
				self._taskChange.notifyAll()
				return self._taskId
			return None
	def __call__(self, *args, **kwargs):
		if self._defaultTarget is not None:
			return self.add(self._defaultTarget, *args, **kwargs)
		else:
			return self.add(args[0], *(args[1:]), **kwargs)
	def _taskFinished(self, thread, task, result, exception):
		with self._lock:
			self._availableThreads.append(thread)
			self._results.append(_getResult(task, result, exception))
			self._numBusy -= 1
			self._taskChange.notifyAll()
	def shutdown(self):
		with self._lock:
			self._shuttingDown = True
			self._taskChange.notifyAll()
			self._shutdownCondition.wait()
			return self._results
	def _getWorkers(self, desired):
		freeWorkers = []
		with self._lock:
			prespawed = min(desired, len(self._availableThreads))
			freeWorkers.extend(self._availableThreads[:prespawed])
			self._availableThreads = self._availableThreads[prespawed:]
			if desired > len(freeWorkers) and self._numSpawned < self._numThreads:
				newWorkers = min(desired - len(freeWorkers), self._numThreads - self._numSpawned)
				for i in xrange(newWorkers):
					freeWorkers.append(_threadpool._poolworker(self))
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

class _multiprocessingpool:
	def __init__(self, numThreads=4, defaultTarget=None):
		self._defaultTarget = defaultTarget
		self._pool = multiprocessing.Pool(numThreads)
		self._lock = threading.RLock()
		self._shuttingDown = False
		self._tasks = []
		self._results = []
		self._taskId = -1
	def add(self, target, *args, **kwargs):
		with self._lock:
			if not self._shuttingDown:
				self._taskId += 1
				self._tasks.append((self._taskId, target, args, kwargs))
				self._results.append(self._pool.apply_async(target, args, kwargs))
				return self._taskId
			return None
	def __call__(self, *args, **kwargs):
		if self._defaultTarget is not None:
			return self.add(self._defaultTarget, *args, **kwargs)
		else:
			return self.add(args[0], *(args[1:]), **kwargs)
	def shutdown(self):
		with self._lock:
			self._shuttingDown = True
			self._pool.close()
			self._pool.join()
			newResults = []
			for task in self._tasks:
				try:
					result = self._results[task[0]].get()
					newResults.append(_getResult(task, result, None))
				except Exception, e:
					newResults.append(_getResult(task, None, e))
			return newResults

def threadpool(numThreads=4, defaultTarget=None, multiprocess=True):
	if multiprocess:
		return _multiprocessingpool(numThreads=numThreads, defaultTarget=defaultTarget)
	return _threadpool(numThreads=numThreads, defaultTarget=defaultTarget)

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
		if random.randint(0, 4) == 2:
			p('Task', i, 'raising a random exception.')
			raise Exception('Random exception')
		returnVal = random.randint(0, 99999)
		p('Task', i, 'finished (sleeping', t, 'seconds), and returning value', returnVal)
		return returnVal
	pool = threadpool(numThreads=2, defaultTarget=dummyTask, multiprocess=False)
	for i in xrange(8):
		t = random.randint(3, 20)
		p('Task', i, 'added (sleeping', t, 'seconds).')
		pool(i, t)
		time.sleep(random.randint(0, 2))
	p('Done adding tasks.')
	results = pool.shutdown()
	p('Pool has shut down.')
	p('Results:')
	for r in results:
		if r['exception'] is None:
			p('Task', r['id'], 'returned', r['result'])
		else:
			p('Task', r['id'], 'raised', r['exception'])
