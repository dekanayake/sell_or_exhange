var gulp = require('gulp');

gulp.task('copy-dependencies', function() {
   return gulp.src(['./node_modules/bootstrap/**/*.*','./node_modules/jquery/**/*.*','./node_modules/font-awesome/**/*.*','./node_modules/dropzone/**/*.*'],{ 'base' : './node_modules' })
   .pipe(gulp.dest('vendor'));
});