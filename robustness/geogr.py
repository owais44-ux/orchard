import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from haversine import haversine, Unit

ITERS = 5
NUM_CLUSTERS = 3
X_RANGE = (67, 125)
X_DIFF = X_RANGE[1]-X_RANGE[0]
Y_RANGE = (25, 49)
Y_DIFF = Y_RANGE[1]-Y_RANGE[0]
global TARGET
global BENIGN_USERS
global ATTACKERS
global avg # number of trials
avg = 10

class User:
	def __init__(self, id, x, y):
		self.id = id
		self.x = x
		self.y = y

	def send_update(self, clusters, t, LDP, defense):
                global TARGET
		if self.id == 'g':
			# Will be an index
			cluster_idx = compute_closest(clusters, self.x, self.y)
			# only have to worry about this if a good guy
			if (LDP == True):
				return (cluster_idx, self.x + np.random.laplace(0, LAP), self.y + np.random.laplace(0, LAP))
			else:
				return (cluster_idx, self.x, self.y)

		else: # if a bad guy!
			
			if defense: #cant do anything right now except for send malicious target (potentially without local noise to help out)
			# assuming no prior knowledge about distribution
				cluster_idx = compute_closest(clusters, self.x, self.y, reverse=False)
                                if t == (ITERS - 1): #just do once, in case TARGET changes over time
                                    TARGET = cluster_idx
				return (cluster_idx, self.x, self.y) 

			else: # can do more sophisticated attack
				if t != (ITERS - 1):
					# confuse with randomness
					#rand_x = np.random.randint(RANGE)
					#rand_y = np.random.randint(RANGE)
					#cluster_idx = compute_closest(clusters, rand_x, rand_y, reverse=False)
					
					cluster_idx = compute_closest(clusters,self.x,self.y, reverse=False)
					return (cluster_idx, self.x, self.y)
					#return (cluster_idx, 0, 0) # Send 0's to make attack easier 
					
				else:
					cluster_idx = compute_closest(clusters, self.x, self.y, reverse=False)
					# Calculate a point which will relocate this cluster to the target
					maliciousInput = compute_mal_point(clusters[cluster_idx], self.x, self.y, LDP)
					TARGET  = cluster_idx
					#print 'Mwahaha --> %d' % TARGET
					
					#print '%d attackers, attacking with (%d, %d)' % (ATTACKERS, maliciousInput[0], maliciousInput[1])
					#print 'Target is (%d, %d)' % (self.x, self.y)

					return (cluster_idx, maliciousInput[0], maliciousInput[1])


def compute_mal_point(cluster, target_x, target_y, LDP):
	estimate = BENIGN_USERS/NUM_CLUSTERS # number of users who choose this cluster
	estimated_sum_x = cluster[0] * (estimate+ATTACKERS) - ATTACKERS * target_x
	estimated_sum_y = cluster[1] * (estimate+ATTACKERS) - ATTACKERS * target_y
	new_x = ((estimate+ATTACKERS) * target_x - estimated_sum_x)/(ATTACKERS)
	new_y = ((estimate+ATTACKERS) * target_y - estimated_sum_y)/(ATTACKERS)
        #print 'OG attack is (%d, %d)' % (new_x, new_y)
	# Clip the result
	if CLIP:
		if LDP: #2x the range to allow for for noise
			return (min(max(X_RANGE[0]-4*X_DIFF,new_x),X_RANGE[1]+4*X_DIFF), min(max(Y_RANGE[0]-4*X_DIFF,new_y),Y_RANGE[1]+4*Y_DIFF))	
		else:
                    return (min(max(X_RANGE[0],new_x),X_RANGE[1]), min(max(Y_RANGE[0],new_y),Y_RANGE[1]))	
	# Non-clipped version	
	else:
		return (new_x, new_y)

# BENIGN FUNCTION
def compute_closest(clusters, x, y, reverse=False):

	min_dist = (clusters[0][0] - x)**2 + (clusters[0][1] - y)**2
	min_idx = 0
	i = 0
	for c in clusters:
		cur_dist = (c[0] - x)**2 + (c[1] - y)**2
		if (cur_dist < min_dist and reverse == False):
			min_dist = cur_dist
			min_idx = i
		# Compute farthest for reverse
		elif (cur_dist > min_dist and reverse == True):
			min_dist = cur_dist
			min_idx = i
		i += 1
	
	return min_idx

def run_protocol(users_list, maliciousTarget, LDP=False, defense=False, benign=False):
	initial_clusters = []

	# Seattle, New York, Houston, in order of (W, N) lat-lon
	cities = [[122.3, 47.6], [74.0, 40.7], [95.4, 29.8]]
	for i in range(NUM_CLUSTERS):
		if RANDOM_INIT==False:
			#initial_clusters.append([X_RANGE[0] + X_DIFF/NUM_CLUSTERS*i, Y_RANGE[0] + Y_DIFF/NUM_CLUSTERS])
			initial_clusters.append(cities[i])
		else:
			initial_clusters.append([np.random.uniform(low=X_RANGE[0], high=X_RANGE[1]), np.random.uniform(low=Y_RANGE[0], high=Y_RANGE[1])])

	#print initial_clusters

	broadcast_clusters = initial_clusters
		
	for t in range(ITERS):
		# rounds of updates
		updated_clusters = [[0,0] for i in range(NUM_CLUSTERS)]
		cluster_counts = [0 for i in range(NUM_CLUSTERS)]
		for u in users_list:
			update = u.send_update(broadcast_clusters, t, LDP, defense)
			
			updated_clusters[update[0]][0] += update[1] # x coord
			updated_clusters[update[0]][1] += update[2] # y coord
			cluster_counts[update[0]] += 1

		for i in range(NUM_CLUSTERS):
			for j in range(2):
				if cluster_counts[i] != 0:
					if (LDP == False): # apply GDP!
						updated_clusters[i][j] += np.random.laplace(0, LAP)
					updated_clusters[i][j] /= cluster_counts[i]
				broadcast_clusters[i][j] = updated_clusters[i][j]
                #l2 norm
		#attackError = abs(updated_clusters[TARGET][0] - maliciousTarget[0])**2/float(RANGE**2) + \
		#    abs(updated_clusters[TARGET][1] - maliciousTarget[1])**2/float(RANGE**2)
                #l1 norm
		#attackError = abs(updated_clusters[TARGET][0] - maliciousTarget[0])/float(RANGE) + \
		    #abs(updateAd_clusters[TARGET][1] - maliciousTarget[1])/float(RANGE)

		#print 'target was %s, cluster was %s' % ( maliciousTarget, updated_clusters[TARGET])
	attackError = haversine(updated_clusters[TARGET], maliciousTarget, unit=Unit.MILES) 

	if (benign == True):
		return updated_clusters
	else:
		return attackError	



def main(exp, rand, eps):
	global TARGET
	TARGET = 0 # initialization
	global BENIGN_USERS
	BENIGN_USERS=10**exp
	global ATTACKERS
	ATTACKERS=0
	global CLIP
	CLIP = False
	global RANDOM_INIT
	RANDOM_INIT=rand
	global EPSILON
	EPSILON=eps
	global LAP
	LAP = 1/EPSILON if EPSILON != 0 else 0
	global EXP
	EXP=exp

	 # FIXING THE DATA OF ALL USERS
        users_list = []
	for i in range(BENIGN_USERS):
		users_list.append(User('g', np.random.uniform(low=X_RANGE[0], high=X_RANGE[1]), np.random.uniform(low=Y_RANGE[0], high=Y_RANGE[1])))

	#maliciousTarget = (np.random.uniform(low=X_RANGE[0], high=X_RANGE[1]), np.random.uniform(low=Y_RANGE[0], high=Y_RANGE[1]))
	maliciousTarget = (80.0, 40.44) # Pittsburgh

	ff = {} # GDP No Defense
	ff_clip = {} # GDP No Defense and clipping
	ft = {} # GDP with defense
	tf = {} # LDP No defense
	tf_clip = {} # LDP No defense and clipping

	attackerOptions = [3**i for i in range(2*EXP+3)]
	#attackerOptions = [1, 10, 100, 1000, 10**4]
	#attackerOptions = [1, 10, 100, 1000, 10**4, 10**5]

	# COMPLETE BENIGN RUN
	#print 'benign clusters would have been: %s' % run_protocol(users_list, maliciousTarget, benign=True)

	for i in range(len(attackerOptions)):
			# Adding new attackers first
			newAttackers = attackerOptions[i] - ATTACKERS
			ATTACKERS = attackerOptions[i]
			for j in range(newAttackers):	
				users_list.append(User('b', maliciousTarget[0], maliciousTarget[1]))

			# Do multiple trials with different initializations / laplace randomness
			for k in range(avg):

				CLIP = False
				err = run_protocol(users_list, maliciousTarget, LDP = False, defense=False)
				if ATTACKERS in ff:
						ff[ATTACKERS].append(err)
				else:
						ff[ATTACKERS] = [err]

				CLIP = True
				err = run_protocol(users_list, maliciousTarget, LDP = False, defense=False)
				if ATTACKERS in ff_clip:
						ff_clip[ATTACKERS].append(err)
				else:
						ff_clip[ATTACKERS] = [err]
				
				CLIP = False
				err = run_protocol(users_list,  maliciousTarget, LDP = False, defense=True)
				if ATTACKERS in ft:
						ft[ATTACKERS].append(err)
				else:
						ft[ATTACKERS] = [err]
				
				CLIP = False
				err = run_protocol(users_list,  maliciousTarget, LDP = True, defense=False)
				if ATTACKERS in tf:
						tf[ATTACKERS].append(err)
				else:
						tf[ATTACKERS] = [err]

				CLIP = True
				err = run_protocol(users_list,  maliciousTarget, LDP = True, defense=False)
				if ATTACKERS in tf_clip:
						tf_clip[ATTACKERS].append(err)
				else:
						tf_clip[ATTACKERS] = [err]


        print exp, rand, eps
        print 'ft:'
        print ft
        print 'ff_clip:'
        print ff_clip
        print 'tf_clip:'
        print tf_clip
        print 'ff:'
        print ff
        print 'tf:'
        print tf

	produce_graph(ff, ff_clip, ft, tf, tf_clip, NUM_CLUSTERS, EPSILON, EXP, RANDOM_INIT)

def errors(x,y):
	yerr = np.zeros([2, len(x)])
	for i in range(len(x)):
		yerr[0][i] = np.median(y,1)[i] - np.percentile(y,25, axis=1)[i]
		yerr[1][i] = np.percentile(y,75,axis=1)[i] - np.median(y,1)[i]
	return yerr
	

def produce_graph(ff, ff_clip, ft, tf, tf_clip, NUM_CLUSTERS, EPSILON, EXP, RANDOM_INIT):
	
	# Formatting
	font = { 
			'size'   : 15}
	matplotlib.rc('font', **font)

	# Sorting the lists annoyance
	fig, ax = plt.subplots()
	ft = sorted(ft.items())
	x, y = zip(*ft)
	#for i in range(avg):
	#	ax.plot(x,[z[i] for z in y],'go',lw=0, label = "GDP w/ defense" if i==0 else "")
	ax.plot(x,np.median(y,1),'go',lw=2,ls='-', label="Orchard" )
        print np.median(y,1)
	yerr = errors(x,y)
	ax.errorbar(x, np.median(y,1), yerr=yerr, marker='o', ls='-', lw=2, color='g', capsize=10)

	ff_clip = sorted(ff_clip.items())
	x, y = zip(*ff_clip)
	#for i in range(avg):
	#	ax.plot(x,[z[i] for z in y],'mo',lw=0, label="GDP + IC" if i==0 else "")
	ax.plot(x,np.median(y,1),'yo',lw=2,ls='-', label="GDP + IC" )
        print np.median(y,1)
	yerr = errors(x,y) 
	ax.errorbar(x, np.median(y,1), yerr=yerr, marker='o', ls='-', lw=2, color='y', capsize=10)

	tf_clip = sorted(tf_clip.items())
	x, y = zip(*tf_clip)
	#for i in range(avg):
	#	ax.plot(x,[z[i] for z in y],'yo',lw=0, label = "LDP + OC" if i==0 else "")
	ax.plot(x,np.median(y,1),'mo',lw=2,ls='-', label="LDP + OC" )
        print np.median(y,1)
	yerr = errors(x,y)
	ax.errorbar(x, np.median(y,1), yerr=yerr, marker='o', ls='-', lw=2, color='m', capsize=10)

	tf = sorted(tf.items())
	x, y = zip(*tf)
	#for i in range(avg):
	#	ax.plot(x,[z[i] for z in y],'ro',lw=0,label = "LDP no defense" if i==0 else "")
	ax.plot(x,np.median(y,1),'ko',lw=2,ls='-', label="LDP no defense" )
        print np.median(y,1)
	yerr = errors(x,y) 
	ax.errorbar(x, np.median(y,1), yerr=yerr, marker='o', ls='-', lw=2, color='black', capsize=10)

        ff = sorted(ff.items())
	x, y = zip(*ff)
	#for i in range(avg):
	#	ax.plot(x,[z[i] for z in y],'bo',lw=0, label="GDP no defense" if i==0 else "")
	ax.plot(x,np.median(y,1),'bo',lw=2,ls='-', label="GDP no defense" )
        print np.median(y,1)
	yerr = errors(x,y) 
	ax.errorbar(x, np.median(y,1), yerr=yerr, marker='o', ls='-', lw=2, color='b', capsize=10)


	
	ax.legend()
	ax.set(xlabel='Number of attackers', ylabel='Attack Error (miles)')
		   #title="Defense Effectiveness")
		   #title="Defense Effectiveness, eps=inf")
	#ax.grid()
	#plt.xticks([pow(10,i) for i in range(3,10)])
        #plt.yticks([0.1*i for i in range(6)])

	#fig.subplots_adjust(left=None, bottom=None, right=None, wspace=None, hspace=0.1)
 	plt.xscale("log")
 	#plt.yscale("log")
 	#plt.legend(loc='upper right', bbox_to_anchor=(-0.2, 0.5),
 	plt.legend(loc='upper right',
           frameon=False, ncol=1, fontsize=10)
	fig.subplots_adjust(bottom=0.2, left=0.3)
	#fig.savefig("defenseFigures/def_k=%d_eps=%0.2f_10^%d%r_extra.png" % (NUM_CLUSTERS, EPSILON, EXP, RANDOM_INIT))
	fig.savefig("defenseFigures/geo_k=%d_eps=%0.2f_10^%d%r_3.png" % (NUM_CLUSTERS, EPSILON, EXP, RANDOM_INIT))
        #fig.savefig("defenseFigures/temp")
	#plt.show()

main(4, False, 0.1)
