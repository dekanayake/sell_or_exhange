var gulp = require('gulp');
var gnf = require('gulp-npm-files');
var sass = require('gulp-sass');


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

gulp.task( 'styles', function () {
          return gulp.src('./vendor/progress-tracker/app/styles/*.scss')
            .pipe(sass().on('error', sass.logError))
            .pipe(gulp.dest('./vendor/progress-tracker/css4'));
} );

