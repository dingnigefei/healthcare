function [] = script()
	load label.dat;
	load depth.dat;
	load joints.dat;
	load topJoints.dat;

	width = 320;
	height = 240;

	label = reshape(label, [width, height])';
	label = mat2gray(label);
	plot2d(label, joints(:, 4:5));

	depth = reshape(depth, [width, height])';
	depth = mat2gray(depth);
	plot2d(depth, joints(:, 4:5));
    
    plot3d(joints(:, 1:3));
    plot3d(topJoints);
    plotProj(joints(:, 1:2));
    plotProj(topJoints(:, 1:2));
end

function [] = plot2d(img, mat)
    figure; 
    imshow(img);
    hold on;
    scatter(mat(:, 1), mat(:, 2));
end

function [] = plotProj(mat)
	figure;
	% JOINT_HEAD
	% JOINT_NECK 	
	% JOINT_LEFT_SHOULDER 	
	% JOINT_RIGHT_SHOULDER 	
	% JOINT_LEFT_ELBOW 	
	% JOINT_RIGHT_ELBOW 	
	% JOINT_LEFT_HAND 	
	% JOINT_RIGHT_HAND 	
	% JOINT_TORSO 	
	% JOINT_LEFT_HIP 	
	% JOINT_RIGHT_HIP 	
	% JOINT_LEFT_KNEE 	
	% JOINT_RIGHT_KNEE 	
	% JOINT_LEFT_FOOT 	
	% JOINT_RIGHT_FOOT 

	pts = [mat(1,:); mat(2,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(2,:); mat(3,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(2,:); mat(4,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(5,:); mat(3,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(6,:); mat(4,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(5,:); mat(7,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(6,:); mat(8,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(9,:); mat(3,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(9,:); mat(4,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(9,:); mat(10,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(9,:); mat(11,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(10,:); mat(11,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(12,:); mat(10,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(13,:); mat(11,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(12,:); mat(14,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	pts = [mat(13,:); mat(15,:)];
	plot(pts(:,1), pts(:,2));
	hold on;

	xlabel('x');
	ylabel('y');
    axis equal;
end

function [] = plot3d(mat)
	figure;
	% JOINT_HEAD
	% JOINT_NECK 	
	% JOINT_LEFT_SHOULDER 	
	% JOINT_RIGHT_SHOULDER 	
	% JOINT_LEFT_ELBOW 	
	% JOINT_RIGHT_ELBOW 	
	% JOINT_LEFT_HAND 	
	% JOINT_RIGHT_HAND 	
	% JOINT_TORSO 	
	% JOINT_LEFT_HIP 	
	% JOINT_RIGHT_HIP 	
	% JOINT_LEFT_KNEE 	
	% JOINT_RIGHT_KNEE 	
	% JOINT_LEFT_FOOT 	
	% JOINT_RIGHT_FOOT 

	pts = [mat(1,:); mat(2,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(2,:); mat(3,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(2,:); mat(4,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(5,:); mat(3,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(6,:); mat(4,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(5,:); mat(7,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(6,:); mat(8,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(9,:); mat(3,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(9,:); mat(4,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(9,:); mat(10,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(9,:); mat(11,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(10,:); mat(11,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(12,:); mat(10,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(13,:); mat(11,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(12,:); mat(14,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	pts = [mat(13,:); mat(15,:)];
	plot3(pts(:,1), pts(:,2), pts(:,3));
	hold on;

	xlabel('x');
	ylabel('y');
	zlabel('z');
    axis equal;
end
