var gulp = require('gulp');
var gnf = require('gulp-npm-files');


gulp.task('copy-npmdependencies', function() {
  gulp
    .src(gnf(null, './package.json'), {base:'./node_modules'})
    .pipe(gulp.dest('./vendor'));
});


gulp.task('copy-nonNpmdependencies', function() {
   return gulp.src(['./nonNPMDependencies/**/*.*'
  ],{ 'base' : './nonNPMDependencies' })
   .pipe(gulp.dest('vendor'));
});