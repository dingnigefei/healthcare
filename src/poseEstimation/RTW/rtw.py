import numpy as np
import pickle
import sys
import argparse
from helper import *
from sklearn.tree import DecisionTreeRegressor
from sklearn.cluster import MiniBatchKMeans
from multiprocessing import Process, Queue

nSamps = 500 # the number of samples of each joint
nFeats = 500 # the number of features of each offset point
maxOffSampXY = 60 # the maximum offset for samples in x, y axes
maxOffSampZ = 2 # the maximum offset for samples in z axis
maxOffFeat = 150 # the maximum offset for features (before divided by d)
largeNum = 100
nSteps = 300
stepSize = 3
K = 20
minSamplesLeaf = 400
trainRatio = 0.7

nJoints = None
jointName = None
C = None

def getInfoEVAL(dataDir, outDir, maxN=None, loadData=False):
    I, joints, theta, bodyCenters = None, None, None, None
    I_train, I_test, joints_train, joints_test = None, None, None, None
    theta, bodyCenters_train, bodyCenters_test = None, None, None

    if loadData:
        I = np.load(outDir+dataDir+'/I.npy')
        I_mask = np.load(outDir+dataDir+'/I_mask.npy')
        I = I*I_mask
        joints = np.load(outDir+dataDir+'/joints.npy')
        theta = np.load(outDir+dataDir+'/theta.npy')
        bodyCenters = np.load(outDir+dataDir+'/bodyCenters.npy')
        N, _, _ = I.shape
    else:
        mkdir(outDir+dataDir)
        # the N x H x W depth images and the N x nJoints x 3 joint locations
        I = np.load(outDir+dataDir+'/I.npy')
        I_mask = np.load(outDir+dataDir+'/I_mask.npy')
        I = I*I_mask
        joints = np.load(outDir+dataDir+'/joints.npy')
        theta = np.random.randint(-maxOffFeat, maxOffFeat+1, (4, nFeats))
        leftHip = (joints[:, 2]+2*joints[:, 8])/3.0
        rightHip = (joints[:, 5]+2*joints[:, 10])/3.0
        bodyCenters = (joints[:, 2]+leftHip+joints[:, 5]+rightHip)/4.0
        np.save(outDir+dataDir+'/theta', theta)
        np.save(outDir+dataDir+'/bodyCenters', bodyCenters)

    print I.shape, joints.shape, theta.shape, bodyCenters.shape
    nTest = I.shape[0]*(1-trainRatio)
    I_test = I[:nTest]
    I_train = I[nTest:]
    joints_test = joints[:nTest]
    joints_train = joints[nTest:]
    bodyCenters_test = bodyCenters[:nTest]
    bodyCenters_train = bodyCenters[nTest:]

    logger.debug('#train: %d, #test: %d', I_train.shape[0], I_test.shape[0])
    return (I_train, I_test, joints_train, joints_test, theta, \
        bodyCenters_train, bodyCenters_test)

def getInfoITOP(depthDir, dataDir, outDir, isTop=False, maxN=None, \
                loadData=False):
    I_train, I_test, joints_train, joints_test = None, None, None, None
    theta, bodyCenters_train, bodyCenters_test = None, None, None

    if loadData:
        I_train = np.load(outDir+dataDir+'/I_train.npy')
        I_test = np.load(outDir+dataDir+'/I_test.npy')
        joints_train = np.load(outDir+dataDir+'/joints_train.npy')
        joints_test = np.load(outDir+dataDir+'/joints_test.npy')
        theta = np.load(outDir+dataDir+'/theta.npy')
        bodyCenters_train = np.load(outDir+dataDir+'/bodyCenters_train.npy')
        bodyCenters_test = np.load(outDir+dataDir+'/bodyCenters_test.npy')
    else:
        mkdir(outDir+dataDir)

        # the N x H x W depth images and the N x nJoints x 3 joint locations
        I_train, I_test, joints_train, joints_test = \
            getImgsAndJointsITOP(depthDir, nJoints, isTop, maxN)

        theta = np.random.randint(-maxOffFeat, maxOffFeat+1, (4, nFeats))
        bodyCenters_train = (joints_train[:, 1]+joints_train[:, 9]+ \
                                joints_train[:, 10])/3
        bodyCenters_test = (joints_test[:, 1]+joints_test[:, 9]+ \
                               joints_test[:, 10])/3

        np.save(outDir+dataDir+'/I_train', I_train)
        np.save(outDir+dataDir+'/I_test', I_test)
        np.save(outDir+dataDir+'/joints_train', joints_train)
        np.save(outDir+dataDir+'/joints_test', joints_test)
        np.save(outDir+dataDir+'/theta', theta)
        np.save(outDir+dataDir+'/bodyCenters_train', bodyCenters_train)
        np.save(outDir+dataDir+'/bodyCenters_test', bodyCenters_test)

    logger.debug('#train: %d, #test: %d', I_train.shape[0], I_test.shape[0])
    return (I_train, I_test, joints_train, joints_test, theta, \
        bodyCenters_train, bodyCenters_test)

'''
    The function creates the training samples.
    Each sample is (i, q, u, f), where i is the index of the depth image, q is
    the random offset point, u is the unit direction vector toward the joint
    location, and f is the feature array.
'''
def getSamples(dataDir, outDir, jointID, theta, I, bodyCenters, joints, \
               loadData=False):
    S_u, S_f = None, None
    nTrain, _, _ = I.shape

    if loadData:
        print outDir+dataDir+'/sf'+str(jointID)+'.npy'
        S_u = np.load(outDir+dataDir+'/su'+str(jointID)+'.npy')
        S_f = np.load(outDir+dataDir+'/sf'+str(jointID)+'.npy')
    else:
        mkdir(outDir+dataDir)

        S_u = np.empty((nTrain, nSamps, 3), dtype=np.float16)
        S_f = np.empty((nTrain, nSamps, nFeats), dtype=np.float16)

        for i in range(nTrain):
            if i%100 == 0:
                logger.debug('joint %s: processing image %d/%d', \
                    jointName[jointID], i, nTrain)
            for j in range(nSamps):
                offsetXY = np.random.randint(-maxOffSampXY, maxOffSampXY+1, 2)
                offsetZ = np.random.uniform(-maxOffSampZ, maxOffSampZ, 1)
                offset = np.concatenate((offsetXY, offsetZ))

                S_u[i, j] = 0 if np.linalg.norm(offset) == 0 else \
                                            -offset/np.linalg.norm(offset)
                S_f[i, j] = getFeatures(I[i], theta, joints[i]+offset, \
                                            bodyCenters[i][2])

        np.save(outDir+dataDir+'/su'+str(jointID), S_u)
        np.save(outDir+dataDir+'/sf'+str(jointID), S_f)

    return (S_u, S_f)

def getFeatures(img, theta, q, z):
    img[img == 0] = largeNum
    coor = q[:2][::-1] # coor: y, x
    coor[0] = np.clip(coor[0], 0, H-1)
    coor[1] = np.clip(coor[1], 0, W-1)
    coor = np.rint(coor).astype(int)
    dq = z if img[tuple(coor)] == largeNum else img[tuple(coor)]

    x1 = np.clip(coor[1]+theta[0]/dq, 0, W-1).astype(int)
    y1 = np.clip(coor[0]+theta[1]/dq, 0, H-1).astype(int)
    x2 = np.clip(coor[1]+theta[2]/dq, 0, W-1).astype(int)
    y2 = np.clip(coor[0]+theta[3]/dq, 0, H-1).astype(int)

    return img[y1, x1] - img[y2, x2]

def stochastic(regressor, features, unitDirections):
    indices = regressor.apply(features) # leaf id of each sample
    leafIDs = np.unique(indices) # array of unique leaf ids
    L = {}

    logger.debug('MiniBatchKMeans...')
    for leafID in leafIDs:
        kmeans = MiniBatchKMeans(n_clusters=K, batch_size=1000)
        labels = kmeans.fit_predict(unitDirections[indices == leafID])
        weights = np.bincount(labels).astype(float)/labels.shape[0]
        centers = kmeans.cluster_centers_
        centers /= np.linalg.norm(centers, axis=1)[:, np.newaxis]
        #checkUnitVectors(centers)

        L[leafID] = (weights, centers)

    return L

def trainModel(X, y, jointID, modelsDir, outDir, loadModels=False):
    regressor, L = None, None

    mkdir(outDir+modelsDir)

    regressorPath = outDir + modelsDir + '/regressor' + str(jointID) + '.pkl'
    LPath = outDir + modelsDir + '/L' + str(jointID) + '.pkl'

    if loadModels and os.path.isfile(regressorPath) and os.path.isfile(LPath):
        logger.debug('loading model %s from files...', jointName[jointID])
        regressor = pickle.load(open(regressorPath, 'rb'))
        L = pickle.load(open(LPath, 'rb'))
    else:
        logger.debug('start training model %s...', jointName[jointID])
        regressor = DecisionTreeRegressor(min_samples_leaf=minSamplesLeaf)

        X_reshape = X.reshape(X.shape[0]*X.shape[1], X.shape[2])
        y_reshape = y.reshape(y.shape[0]*y.shape[1], y.shape[2])

        rows = np.logical_not(np.all(X_reshape == 0, axis=1))
        regressor.fit(X_reshape[rows], y_reshape[rows])
        logger.debug('model %s - valid samples: %d/%d', jointName[jointID], \
            X_reshape[rows].shape[0], X_reshape.shape[0])

        leafIDs = regressor.apply(X_reshape)
        bin = np.bincount(leafIDs)
        uniqueIDs = np.unique(leafIDs)
        biggest = np.argmax(bin)
        smallest = np.argmin(bin[bin != 0])

        logger.debug('model %s - #leaves: %d', jointName[jointID], \
                     uniqueIDs.shape[0])
        logger.debug('model %s - biggest leaf id: %d, #samples: %d/%d', \
                     jointName[jointID], biggest, bin[biggest], np.sum(bin))
        logger.debug('model %s - smallest leaf id: %d, #samples: %d/%d', \
                     jointName[jointID], smallest, bin[bin != 0][smallest], \
                     np.sum(bin))
        logger.debug('model %s - average leaf size: %d', jointName[jointID], \
                     np.sum(bin)/uniqueIDs.shape[0])

        L = stochastic(regressor, X_reshape, y_reshape)

        pickle.dump(regressor, open(regressorPath, 'wb'))
        pickle.dump(L, open(LPath, 'wb'))

    return (regressor, L)

def testModel(regressor, L, theta, qm0, img, bodyCenter):
    qm = np.zeros((nSteps+1, 3))
    qm[0] = qm0
    joint_pred = np.zeros(3)

    for i in range(nSteps):
        f = getFeatures(img, theta, qm[i], bodyCenter[2]).reshape(1, -1)
        leafID = regressor.apply(f)[0]

        # L[leafID][0]: weights, L[leafID][1]: centers
        idx = np.random.choice(K, p=L[leafID][0])
        u = L[leafID][1][idx]

        qm[i+1] = qm[i] + u*stepSize
        qm[i+1][0] = np.clip(qm[i+1][0], 0, W-1)
        qm[i+1][1] = np.clip(qm[i+1][1], 0, H-1)
        qm[i+1][2] = img[int(qm[i+1][1]), int(qm[i+1][0])]
        joint_pred += qm[i+1]

    joint_pred = joint_pred/nSteps

    return (qm, joint_pred)

def getDists(joints, joints_pred):
    assert joints.shape == joints_pred.shape
    dists = np.zeros((joints.shape[:2]))

    for i in range(joints.shape[0]):
        p1 = pixel2world(joints[i], C)
        p2 = pixel2world(joints_pred[i], C)
        dists[i] = np.sqrt(np.sum((p1-p2)**2, axis=1))
    return dists

def trainParallel(dataDir, modelsDir, outDir, jointID, theta, I, bodyCenters, \
                  joints, loadData, loadModels, regressorQ, LQ):
    S_u, S_f = getSamples(dataDir, outDir, jointID, theta, I, bodyCenters, \
                                                joints, loadData)

    regressor, L = trainModel(S_f, S_u, jointID, modelsDir, outDir, loadModels)
    regressorQ.put({jointID: regressor})
    LQ.put({jointID: L})

def trainSeries(dataDir, modelsDir, outDir, jointID, theta, I, bodyCenters, \
                joints, loadData, loadModels):
    S_u, S_f = getSamples(dataDir, outDir, jointID, theta, I, bodyCenters, \
                                                joints, loadData)
    regressor, L = trainModel(S_f, S_u, jointID, modelsDir, outDir, loadModels)
    return (regressor, L)

def main(**kwargs):
    global nJoints
    global jointName
    global C
    #depthDir = argv[0] + '/*/joints_depthcoor/*'
    #depthDir = ''#argv[0] #'/mnt0/data/ITOP/out'
    #outDir = ''#argv[1]

    loadData = kwargs.get('loaddata')
    loadModels = kwargs.get('loadmodels')
    loadTest = kwargs.get('loadtest')
    dataDir = kwargs.get('data')
    modelsDir = kwargs.get('models')
    ITOP = kwargs.get('itop')
    isTop = kwargs.get('top')
    depthDir = kwargs.get('indir')
    outDir = kwargs.get('outdir')
    makePng = kwargs.get('png')
    maxN = kwargs.get('maxn')
    multiThreads = kwargs.get('multithreads')

    nJoints = 15 if ITOP else 12
    jointName = jointNameITOP if ITOP else jointNameEVAL
    C = 3.50666662e-3 if ITOP else 3.8605e-3

    '''
    for i, arg in enumerate(argv[2:]):
        if arg == '-loaddata':
            loadData = True
        elif arg == '-loadmodels':
            loadModels = True
        elif arg == '-maxn':
            maxN = int(argv[2:][i+1])
            print 'maxN: %d' % maxN
        elif arg == '-multithreads':
            multiThreads = True
        elif arg == '-png':
            makePng = True
    '''

    if ITOP:
        I_train, I_test, joints_train, joints_test, theta, bodyCenters_train, \
            bodyCenters_test = getInfoITOP(depthDir, dataDir, outDir, isTop, \
            maxN, loadData)
    else:
        I_train, I_test, joints_train, joints_test, theta, bodyCenters_train, \
            bodyCenters_test = getInfoEVAL(dataDir, outDir, maxN, \
            loadData)

    nTrain = I_train.shape[0]
    nTest = I_test.shape[0]

    regressors, Ls = {}, {}
    if not loadTest:
        logger.debug('\n------- training models -------')
        if multiThreads:
            processes = []
            regressorQ, LQ = Queue(), Queue()

            for i in range(nJoints):
                p = Process(target=trainParallel, name='Thread #%d' % i, \
                            args=(dataDir, modelsDir, outDir, i, theta, \
                            I_train, bodyCenters_train, joints_train[:, i], \
                            loadData, loadModels, regressorQ, LQ))
                processes.append(p)
                p.start()

            regressorsTmp = [regressorQ.get() for p in processes]
            LsTmp = [LQ.get() for p in processes]
            regressors = dict(i.items()[0] for i in regressorsTmp)
            Ls = dict(i.items()[0] for i in LsTmp)

            [p.join() for p in processes]
        else:
            for i in range(nJoints):
                regressors[i], Ls[i] = trainSeries(dataDir, modelsDir, outDir, \
                                           i, theta, I_train, \
                                           bodyCenters_train, \
                                           joints_train[:, i], \
                                           loadData, loadModels)

    logger.debug('\n------- testing models -------')
    qms = np.zeros((nTest, nJoints, nSteps+1, 3))
    joints_pred = np.zeros((nTest, nJoints, 3))
    localErr = np.zeros((nTest, nSteps+1, nJoints, 3))
    kinemOrder, kinemParent = None, None

    if ITOP:
        kinemOrder = kinemOrderITOP
        kinemParent = kinemParentITOP
    else:
        kinemOrder = kinemOrderEVAL
        kinemParent = kinemParentEVAL

    if loadTest:
        qms = np.load(outDir+modelsDir+'/qms.npy')
        joints_pred = np.load(outDir+modelsDir+'/joints_pred.npy')
        localErr = np.load(outDir+modelsDir+'/local_err.npy')
    else:
        for idx, jointID in enumerate(kinemOrder):
            logger.debug('testing model %s', jointName[jointID])
            for i in range(nTest):
                qm0 = bodyCenters_test[i] if kinemParent[idx] == -1 \
                    else joints_pred[i][kinemParent[idx]]
                qms[i][jointID], joints_pred[i][jointID] = testModel(
                    regressors[jointID], Ls[jointID], theta, qm0, I_test[i], \
                    bodyCenters_test[i])
                localErr[i, :, jointID, :] = joints_test[i, jointID] - qms[i][jointID]

        np.save(outDir+modelsDir+'/qms', qms)
        np.save(outDir+modelsDir+'/joints_pred', joints_pred)
        np.save(outDir+modelsDir+'/local_err.npy', localErr)

    mkdir(outDir+modelsDir+'/pred/')
    for jointID in range(nJoints):
        #print joints_test[:, jointID].shape
        np.savetxt(outDir+modelsDir+'/pred/'+jointName[jointID]+'_test.txt', \
            joints_test[:, jointID], fmt='%.3f')
        #print joints_pred[:, jointID].shape
        np.savetxt(outDir+modelsDir+'/pred/'+jointName[jointID]+'_pred.txt', \
            joints_pred[:, jointID], fmt='%.3f ')
    joints_pred[:, :, 2] = joints_test[:, :, 2]
    dists = getDists(joints_test, joints_pred)*100.0
    np.savetxt(outDir+modelsDir+'/pred/dists.txt', dists, fmt='%.3f')

    #distsPixel = np.zeros((joints.shape[:2]))
    #for i in range(joints.shape[0]):
    #    p1 = joints[i]
    #    p2 = joints_pred[i]
    #    distsPixel[i] = np.sqrt(np.sum((p1-p2)**2, axis=1))

    mAP = 0
    for i in range(nJoints):
        logger.debug('\nJoint %s:', jointName[i])
        logger.debug('average distance: %f cm', np.mean(dists[:, i]))
        #logger.debug('average pixel distance: %f', np.mean(distsPixel[:, i]))
        logger.debug('5cm accuracy: %f', np.sum(dists[:, i] < 5)/ \
            float(dists.shape[0]))
        logger.debug('10cm accuracy: %f', np.sum(dists[:, i] < 10)/ \
            float(dists.shape[0]))
        logger.debug('15cm accuracy: %f', np.sum(dists[:, i] < 15)/ \
            float(dists.shape[0]))
        mAP += np.sum(dists[:, i] < 10)/float(dists.shape[0])
    logger.debug('mAP (10cm): %f', mAP/nJoints)

    # visualize predicted labels
    if not makePng:
        return

    mkdir(outDir+dataDir+'/png/')
    for i in range(nTest):
        pngPath = outDir+dataDir+'/png/'+str(i)+'.png'
        drawPred(I_test[i], joints_pred[i], qms[i], bodyCenters_test[i], \
                 pngPath, nJoints, jointName, isTop)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--loadmodels', action='store_true')
    parser.add_argument('--loaddata', action='store_true')
    parser.add_argument('--loadtest', action='store_true')
    parser.add_argument('--models')
    parser.add_argument('--data')
    parser.add_argument('--indir')
    parser.add_argument('--outdir')
    parser.add_argument('--itop', action='store_true')
    parser.add_argument('--top', action='store_true')
    parser.add_argument('--png', action='store_true')
    parser.add_argument('--multithreads', action='store_true')
    parser.add_argument('--maxn', type=int)
    args = parser.parse_args()
    main(**vars(args))
