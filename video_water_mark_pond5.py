import cv2 as cv
import numpy as np
import time
import os


def get_alpha_W_black():
	video = "videos/pond5-black.mp4"
	cap = cv.VideoCapture(video)
	res, waterpic = cap.read()
	# cv.imshow("waterpic_black", waterpic)
	waterpic = waterpic.max(axis=-1)
	# print(np.bincount(waterpic.reshape(-1),minlength=256))
	# cv.imshow("range", ((waterpic>10)&(waterpic<200)).astype(np.float))

	alpha_0 = 104/255
	thresh = 85
	waterpic[waterpic<thresh] = 0
	waterpic[waterpic>=thresh] = 104
	# cv.imshow("waterpic_black_2", waterpic.astype(np.uint8))

	alpha = np.ones(waterpic.shape) * alpha_0
	alpha[waterpic==0] = 0
	W = waterpic/alpha_0
	# cv.imshow("black  alpha,W",np.vstack([alpha*255, W]).astype(np.uint8))
	test_img1 = ((1-alpha)*np.zeros(W.shape) + alpha*W).astype(np.uint8)
	# print(np.bincount(test_img1.reshape(-1), minlength=256))
	# cv.imshow("test_img", test_img1)
	# cv.waitKey(0)

	alpha = np.repeat(alpha, 3, axis=-1).reshape(*(alpha.shape),3)
	W = np.repeat(W, 3, axis=-1).reshape(*(W.shape),3)
	return alpha, W

def blur_mask(alpha, W):
	video = "videos/pond5-black.mp4"
	cap = cv.VideoCapture(video)
	difs = []
	if True:
		index = 0
		while True:
			result, frame = cap.read()
			if not result: break
			index += 1
			# if index % 3 != 0:continue

			I = (frame.astype(float) - alpha * W)/(1-alpha)
			# cv.imshow("sub result",(frame.astype(float) - alpha * W).astype(np.uint8))
			# print(frame[alpha!=0].min(), frame[alpha!=0].max(), )
			# print(I.min(),I.max(),alpha.shape,len(I[I<0]), np.mean(I[I<0]), len(I[I>255]), np.mean(I[I>255]))
			# print(frame[I>255][0:2], alpha[I>255][0:2], W[I>255][0:2], I[I>255][0:2])

			I[I>255]=255
			I[I<0] = 0
			I = I.astype(np.uint8)
			fI = I.copy()
			fI = cv.medianBlur(fI, 5)

			oboximage = frame
			iboximage = I
			fboximage = fI

			dif = np.abs(fboximage.astype(float)-iboximage.astype(float))
			difs.append(dif)

			# cv.rectangle(I,(box[1],box[0]),(box[3],box[2]),(0, 255, 255),1,8)

			# cv.imshow("diffenence", np.vstack([oboximage,iboximage,fboximage,
			#   dif.astype(np.uint8),np.median(np.array(difs),axis=0).astype(np.uint8)]))
			# cv.waitKey(0)

			# if index==100:break
			# break
		np.save("med.npy", np.array(difs))

	difs = np.load("med.npy")

	difs = difs.astype(np.uint8)
	if False:
		med = np.zeros(difs[0].shape[0:2], dtype=np.uint8)
		for i in range(med.shape[0]):
			for j in range(med.shape[1]):
				med[i,j] = np.bincount(difs[:,i,j,:].reshape(-1),minlength=256).argmax()
	else:
		med = np.median(difs,axis=0).astype(np.uint8)
		med = med.max(axis=-1)
		med[med<30] = 0
	print(med.shape)
	med = np.repeat(med, 3, axis=-1).reshape(*(med.shape),3)

	# cv.imshow("dif", med)

	bg = med

	# cv.imshow("bg", bg.astype(np.uint8)+(alpha*100).astype(np.uint8))
	# cv.imshow("bg", bg.astype(np.uint8))
	# cv.waitKey(0)
	return bg


def process_video(video, alpha, W, bg, out_video=None):
	cap = cv.VideoCapture(video)
	if out_video is not None:
		video_FourCC= int(cap.get(cv.CAP_PROP_FOURCC))
		video_fps   = cap.get(cv.CAP_PROP_FPS)
		video_size  = (int(cap.get(cv.CAP_PROP_FRAME_WIDTH)),
					   int(cap.get(cv.CAP_PROP_FRAME_HEIGHT)))
		vwriter = cv.VideoWriter(out_video, video_FourCC,
								 video_fps, video_size, isColor=True)
	else:
		select = set(range(1,1000,30))

	accum_time = 0.000001
	index = 0
	while True:
		res, frame = cap.read()
		if not res:break
		if frame.shape!=(360,640,3):
			break
		start = time.time()

		index += 1
		if index==1:

			pos = alpha.nonzero()
			box = [pos[0].min(), pos[1].min(), pos[0].max(), pos[1].max()]
			ROI = np.ix_(range(box[0]-5,box[2]+5), range(box[1]-5,box[3]+5))
			aW = (alpha*W)[ROI]
			a1 = (1/(1 - alpha))[ROI]
			med = bg[ROI]

		if out_video is None and index not in select:continue

		org_frame = frame.copy()
		frame = frame.astype(np.float)
		J = frame[ROI]
		I = (J - aW) * a1
		I[I<0] = 0
		I[I>255] = 255
		frame[ROI] = I

		sub_frame = frame.copy().astype(np.uint8)

		fI = I.copy()
		fI = cv.medianBlur(fI.astype(np.uint8), 5)
		I[med!=0] = fI[med!=0]
		I[I<0] = 0
		I[I>255] = 255
		frame[ROI] = I
		frame = frame.astype(np.uint8)

		accum_time += time.time() - start
		print("frame:", index,"fps:", index/accum_time)

		# cv.imwrite("imgs/pond5_orig.png",org_frame)
		# cv.imwrite("imgs/pond5_subs.png",sub_frame)
		# cv.imwrite("imgs/pond5_res.png",frame)

		cv.imshow("frame", np.vstack([org_frame,frame]))
		cv.waitKey(0)
		if out_video:vwriter.write(frame)
		
	cap.release()
	if out_video:vwriter.release()

def main():
	alpha, W = get_alpha_W_black()
	bg = blur_mask(alpha, W)

	# cv.imwrite("imgs/pond5_alpha.png", (alpha*255).astype(np.uint8))
	# cv.imwrite("imgs/pond5_W.png", (W).astype(np.uint8))

	video = "videos/pond5-black.mp4"
	process_video(video, alpha, W, bg)

	return
	dirname = "/database/水印视频/pond5/"
	for root, dirs, names in os.walk(dirname):
		if dirs==[]:
			os.makedirs(root.replace("水印视频", "去水印视频"), exist_ok=True)
			for name in names:
				video = root+"/"+name
				out_video = root.replace("水印视频", "去水印视频")+"/"+name
				print(video)
				if not os.path.exists(out_video):
					process_video(video, alpha, W, bg, out_video)


if __name__ == '__main__':
	main()
